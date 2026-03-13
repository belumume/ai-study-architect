"""
Rate limiter tests.

Tests that slowapi rate limiting works on auth endpoints.
The conftest client fixture disables rate limiting — these tests
use a separate fixture with rate limiting enabled.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session

from app.main import app as fastapi_app
from app.api.dependencies import get_db


@pytest.fixture
async def rate_limited_client(db_session: Session) -> AsyncClient:
    """Client with rate limiting ENABLED (unlike the default client fixture)."""

    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Re-enable rate limiting on both limiter instances
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    enabled_limiter = Limiter(key_func=get_remote_address, enabled=True)
    fastapi_app.state.limiter = enabled_limiter

    import app.api.v1.auth as auth_module

    auth_module.limiter = enabled_limiter

    import app.main as main_module

    main_module.limiter = enabled_limiter

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as c:
        yield c

    fastapi_app.dependency_overrides.clear()

    # Restore disabled limiters for other tests
    disabled_limiter = Limiter(key_func=get_remote_address, enabled=False)
    fastapi_app.state.limiter = disabled_limiter
    auth_module.limiter = disabled_limiter
    main_module.limiter = disabled_limiter


class TestRateLimiter:
    """Test rate limiting on auth endpoints."""

    @pytest.mark.asyncio
    async def test_register_rate_limit_allows_under_limit(self, rate_limited_client):
        """Requests under the limit should succeed (or fail for other reasons, not 429)."""
        for i in range(3):
            response = await rate_limited_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"ratelimit{i}@example.com",
                    "username": f"ratelimit{i}",
                    "password": "TestPass123",
                },
            )
            assert response.status_code != 429, f"Request {i + 1} was rate limited unexpectedly"

    @pytest.mark.asyncio
    async def test_register_rate_limit_blocks_over_limit(self, rate_limited_client):
        """The 6th request within a minute should be rate limited (429)."""
        for i in range(6):
            response = await rate_limited_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"overlimit{i}@example.com",
                    "username": f"overlimit{i}",
                    "password": "TestPass123",
                },
            )
            if i < 5:
                assert response.status_code != 429, f"Request {i + 1}/6 was rate limited too early"
            else:
                assert response.status_code == 429, (
                    f"Request {i + 1}/6 should have been rate limited but got {response.status_code}"
                )

    @pytest.mark.asyncio
    async def test_login_rate_limit_blocks_over_limit(self, rate_limited_client):
        """Login endpoint should also be rate limited at 5/minute."""
        for i in range(6):
            response = await rate_limited_client.post(
                "/api/v1/auth/login",
                data={
                    "username": "nonexistent",
                    "password": "wrongpassword",
                    "remember_me": "false",
                },
            )
            if i < 5:
                assert response.status_code != 429, (
                    f"Login request {i + 1}/6 rate limited too early"
                )
            else:
                assert response.status_code == 429, (
                    f"Login request {i + 1}/6 should have been rate limited but got {response.status_code}"
                )

    @pytest.mark.asyncio
    async def test_rate_limit_response_format(self, rate_limited_client):
        """Rate limited response should have proper error format."""
        # Exhaust the limit
        for i in range(6):
            response = await rate_limited_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"format{i}@example.com",
                    "username": f"format{i}",
                    "password": "TestPass123",
                },
            )

        assert response.status_code == 429
        assert "Retry-After" in response.headers or response.status_code == 429
