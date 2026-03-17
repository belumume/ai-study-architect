"""
Tests for refresh endpoint improvements:
- Todo 047: Redis error should not be treated as token theft
- Todo 048: Refresh should preserve session cookie type (remember_me)
"""

import hashlib
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.cache import CacheResult
from app.core.security import (
    create_refresh_token,
    get_password_hash,
    verify_token_claims,
)
from app.models.user import User


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class TestRefreshRedisErrorHandling:
    """Todo 047: Redis transient errors should not lock users out"""

    @pytest.mark.asyncio
    async def test_redis_error_skips_replay_detection(
        self, client: AsyncClient, db_session: Session
    ):
        """When Redis has a transient error during refresh, skip replay detection
        instead of rejecting the token as stolen."""
        user = User(
            email="redis_err@example.com",
            username="redis_err_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        family_id = "test_family_abc"
        refresh_tok = create_refresh_token(subject=str(user.id), family_id=family_id)

        # Mock Redis as connected but get_with_status returns an error
        with patch("app.api.v1.auth.redis_cache") as mock_cache:
            mock_cache.is_connected = True
            mock_cache._get_client.return_value = mock_cache
            # Simulate transient Redis error
            mock_cache.get_with_status.return_value = CacheResult(
                value=None, found=False, error=True
            )
            # set() for storing the new family hash
            mock_cache.set.return_value = True

            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_tok}
            )

        # Should succeed — not reject as theft
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_invalidated_family_still_rejects(self, client: AsyncClient, db_session: Session):
        """When Redis returns not-found (family genuinely invalidated), reject."""
        user = User(
            email="inv_family@example.com",
            username="inv_family_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        family_id = "invalidated_family"
        refresh_tok = create_refresh_token(subject=str(user.id), family_id=family_id)

        with patch("app.api.v1.auth.redis_cache") as mock_cache:
            mock_cache.is_connected = True
            mock_cache._get_client.return_value = mock_cache
            # Family key genuinely missing (not an error)
            mock_cache.get_with_status.return_value = CacheResult(
                value=None, found=False, error=False
            )

            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_tok}
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_replay_detection_still_works(self, client: AsyncClient, db_session: Session):
        """When Redis returns a different hash (token was consumed), reject as replay."""
        user = User(
            email="replay_det@example.com",
            username="replay_det_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        family_id = "replay_family"
        refresh_tok = create_refresh_token(subject=str(user.id), family_id=family_id)

        with patch("app.api.v1.auth.redis_cache") as mock_cache:
            mock_cache.is_connected = True
            mock_cache._get_client.return_value = mock_cache
            # Return a different hash (token was already consumed)
            mock_cache.get_with_status.return_value = CacheResult(
                value="different_hash_from_newer_token", found=True, error=False
            )
            mock_cache.delete.return_value = True

            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_tok}
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_hash_match_succeeds(self, client: AsyncClient, db_session: Session):
        """When Redis returns the correct hash, refresh succeeds."""
        user = User(
            email="hash_match@example.com",
            username="hash_match_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        family_id = "valid_family"
        refresh_tok = create_refresh_token(subject=str(user.id), family_id=family_id)
        token_hash = _hash_token(refresh_tok)

        with patch("app.api.v1.auth.redis_cache") as mock_cache:
            mock_cache.is_connected = True
            mock_cache._get_client.return_value = mock_cache
            # Return the correct hash — the token is the current valid one
            mock_cache.get_with_status.return_value = CacheResult(
                value=token_hash, found=True, error=False
            )
            mock_cache.set.return_value = True

            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_tok}
            )

        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"


class TestRefreshRememberMe:
    """Todo 048: Refresh should preserve session cookie type"""

    @pytest.mark.asyncio
    async def test_remember_me_true_sets_max_age(self, client: AsyncClient, db_session: Session):
        """When remember_me=True in the refresh token, cookies should have max_age."""
        user = User(
            email="rem_true@example.com",
            username="rem_true_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create refresh token with remember_me=True (persistent)
        refresh_tok = create_refresh_token(subject=str(user.id), remember_me=True)

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_tok})

        assert response.status_code == 200

        # Check Set-Cookie headers for max-age
        raw_headers = response.headers.get_list("set-cookie")
        access_cookie = [h for h in raw_headers if h.startswith("access_token=")]
        refresh_cookie = [h for h in raw_headers if h.startswith("refresh_token=")]

        assert len(access_cookie) == 1, "Expected access_token Set-Cookie header"
        assert len(refresh_cookie) == 1, "Expected refresh_token Set-Cookie header"

        # Persistent cookies should have Max-Age
        assert "max-age=" in access_cookie[0].lower(), (
            "access_token cookie should have max-age for remember_me=True"
        )
        assert "max-age=" in refresh_cookie[0].lower(), (
            "refresh_token cookie should have max-age for remember_me=True"
        )

    @pytest.mark.asyncio
    async def test_remember_me_false_omits_max_age(self, client: AsyncClient, db_session: Session):
        """When remember_me=False in the refresh token, cookies should be session cookies
        (no max_age)."""
        user = User(
            email="rem_false@example.com",
            username="rem_false_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create refresh token with remember_me=False (session cookie)
        refresh_tok = create_refresh_token(subject=str(user.id), remember_me=False)

        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_tok})

        assert response.status_code == 200

        # Check Set-Cookie headers — session cookies should NOT have max-age
        raw_headers = response.headers.get_list("set-cookie")
        access_cookie = [h for h in raw_headers if h.startswith("access_token=")]
        refresh_cookie = [h for h in raw_headers if h.startswith("refresh_token=")]

        assert len(access_cookie) == 1, "Expected access_token Set-Cookie header"
        assert len(refresh_cookie) == 1, "Expected refresh_token Set-Cookie header"

        assert "max-age=" not in access_cookie[0].lower(), (
            "access_token cookie should NOT have max-age for remember_me=False"
        )
        assert "max-age=" not in refresh_cookie[0].lower(), (
            "refresh_token cookie should NOT have max-age for remember_me=False"
        )

    @pytest.mark.asyncio
    async def test_legacy_token_without_rem_defaults_to_persistent(
        self, client: AsyncClient, db_session: Session
    ):
        """Legacy tokens without 'rem' claim should default to persistent cookies."""
        user = User(
            email="legacy_rem@example.com",
            username="legacy_rem_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Patch create_refresh_token to NOT include 'rem' claim (simulating legacy token)
        from datetime import timedelta

        from jose import jwt

        from app.core.config import settings
        from app.core.security import get_current_keys
        from app.core.utils import utcnow

        expire = utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        current_keys = get_current_keys()
        kid = current_keys.get("key_id", "fallback")
        # Include fid but omit rem — this is the realistic backward-compat case
        # (tokens created with rotation but before rem was added)
        import uuid

        family_id = uuid.uuid4().hex
        payload = {
            "exp": expire,
            "sub": str(user.id),
            "type": "refresh",
            "fid": family_id,
            # No "rem" claim — legacy token with rotation
        }
        if current_keys.get("private"):
            legacy_token = jwt.encode(
                payload, current_keys["private"], algorithm="RS256", headers={"kid": kid}
            )
        else:
            legacy_token = jwt.encode(
                payload, settings.JWT_SECRET_KEY, algorithm="HS256", headers={"kid": kid}
            )

        # Mock Redis: token has fid, so refresh will check Redis for family hash
        token_hash = _hash_token(legacy_token)
        with patch("app.api.v1.auth.redis_cache") as mock_cache:
            mock_cache.is_connected = True
            mock_cache._get_client.return_value = mock_cache
            mock_cache.get_with_status.return_value = CacheResult(
                value=token_hash, found=True, error=False
            )
            mock_cache.set.return_value = True

            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": legacy_token}
            )

        assert response.status_code == 200

        # Legacy tokens default to remember_me=True → persistent cookies with max-age
        raw_headers = response.headers.get_list("set-cookie")
        access_cookie = [h for h in raw_headers if h.startswith("access_token=")]
        refresh_cookie = [h for h in raw_headers if h.startswith("refresh_token=")]

        assert len(access_cookie) == 1
        assert len(refresh_cookie) == 1
        assert "max-age=" in access_cookie[0].lower()
        assert "max-age=" in refresh_cookie[0].lower()

    @pytest.mark.asyncio
    async def test_true_legacy_token_no_fid_no_rem_defaults_to_persistent(
        self, client: AsyncClient, db_session: Session
    ):
        """Tokens from before rotation (no fid, no rem) should also default to persistent."""
        user = User(
            email="true_legacy@example.com",
            username="true_legacy_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        from datetime import timedelta

        from jose import jwt

        from app.core.config import settings
        from app.core.security import get_current_keys
        from app.core.utils import utcnow

        expire = utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        current_keys = get_current_keys()
        kid = current_keys.get("key_id", "fallback")
        # No fid, no rem — true pre-rotation legacy token
        payload = {
            "exp": expire,
            "sub": str(user.id),
            "type": "refresh",
        }
        if current_keys.get("private"):
            legacy_token = jwt.encode(
                payload, current_keys["private"], algorithm="RS256", headers={"kid": kid}
            )
        else:
            legacy_token = jwt.encode(
                payload, settings.JWT_SECRET_KEY, algorithm="HS256", headers={"kid": kid}
            )

        # No fid → skips Redis validation, migrates to new family
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": legacy_token})

        assert response.status_code == 200

        raw_headers = response.headers.get_list("set-cookie")
        access_cookie = [h for h in raw_headers if h.startswith("access_token=")]
        refresh_cookie = [h for h in raw_headers if h.startswith("refresh_token=")]

        assert len(access_cookie) == 1
        assert len(refresh_cookie) == 1
        assert "max-age=" in access_cookie[0].lower()
        assert "max-age=" in refresh_cookie[0].lower()

    def test_create_refresh_token_embeds_rem_claim(self):
        """create_refresh_token should embed the 'rem' claim."""
        token_true = create_refresh_token(subject="user1", remember_me=True)
        claims_true = verify_token_claims(token_true, token_type="refresh")
        assert claims_true is not None
        assert claims_true["rem"] is True

        token_false = create_refresh_token(subject="user2", remember_me=False)
        claims_false = verify_token_claims(token_false, token_type="refresh")
        assert claims_false is not None
        assert claims_false["rem"] is False

    def test_create_refresh_token_defaults_to_remember_me_true(self):
        """Default remember_me should be True for backward compatibility."""
        token = create_refresh_token(subject="user3")
        claims = verify_token_claims(token, token_type="refresh")
        assert claims is not None
        assert claims["rem"] is True

    @pytest.mark.asyncio
    async def test_login_remember_me_false_then_refresh_preserves(
        self, client: AsyncClient, db_session: Session
    ):
        """Full flow: login with remember_me=false, refresh should keep session cookies."""
        user = User(
            email="flow_sess@example.com",
            username="flow_sess_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # Login without remember_me
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "flow_sess@example.com",
                "password": "password123",
                "remember_me": "false",
            },
        )
        assert login_resp.status_code == 200

        # Verify the refresh token has rem=False
        refresh_cookie = login_resp.cookies.get("refresh_token")
        assert refresh_cookie is not None
        claims = verify_token_claims(refresh_cookie, token_type="refresh")
        assert claims is not None
        assert claims.get("rem") is False

        # Now refresh using that cookie
        client.cookies.set("refresh_token", refresh_cookie)
        refresh_resp = await client.post("/api/v1/auth/refresh")
        assert refresh_resp.status_code == 200

        # Refreshed cookies should also be session cookies (no max-age)
        raw_headers = refresh_resp.headers.get_list("set-cookie")
        access_cookie_hdr = [h for h in raw_headers if h.startswith("access_token=")]
        refresh_cookie_hdr = [h for h in raw_headers if h.startswith("refresh_token=")]

        assert len(access_cookie_hdr) == 1
        assert len(refresh_cookie_hdr) == 1
        assert "max-age=" not in access_cookie_hdr[0].lower()
        assert "max-age=" not in refresh_cookie_hdr[0].lower()

        # And the new refresh token should still have rem=False
        new_refresh = refresh_resp.cookies.get("refresh_token")
        assert new_refresh is not None
        new_claims = verify_token_claims(new_refresh, token_type="refresh")
        assert new_claims is not None
        assert new_claims.get("rem") is False

    @pytest.mark.asyncio
    async def test_login_remember_me_true_then_refresh_preserves(
        self, client: AsyncClient, db_session: Session
    ):
        """Full flow: login with remember_me=true, refresh should keep persistent cookies."""
        user = User(
            email="flow_pers@example.com",
            username="flow_pers_user",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # Login with remember_me
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "flow_pers@example.com",
                "password": "password123",
                "remember_me": "true",
            },
        )
        assert login_resp.status_code == 200

        # Verify the refresh token has rem=True
        refresh_cookie = login_resp.cookies.get("refresh_token")
        assert refresh_cookie is not None
        claims = verify_token_claims(refresh_cookie, token_type="refresh")
        assert claims is not None
        assert claims.get("rem") is True

        # Refresh
        client.cookies.set("refresh_token", refresh_cookie)
        refresh_resp = await client.post("/api/v1/auth/refresh")
        assert refresh_resp.status_code == 200

        # Persistent cookies should have max-age
        raw_headers = refresh_resp.headers.get_list("set-cookie")
        access_cookie_hdr = [h for h in raw_headers if h.startswith("access_token=")]
        refresh_cookie_hdr = [h for h in raw_headers if h.startswith("refresh_token=")]

        assert len(access_cookie_hdr) == 1
        assert len(refresh_cookie_hdr) == 1
        assert "max-age=" in access_cookie_hdr[0].lower()
        assert "max-age=" in refresh_cookie_hdr[0].lower()
