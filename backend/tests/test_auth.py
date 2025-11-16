"""
Authentication endpoint tests
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)


class TestUserRegistration:
    """Test user registration endpoint"""

    @pytest.mark.asyncio
    async def test_register_new_user_success(self, client: AsyncClient):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser123",
            "full_name": "New User",
            "password": "securepassword123"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "hashed_password" not in data  # Password should not be returned

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, db_session: AsyncSession):
        """Test registration with duplicate email"""
        # Create existing user
        existing_user = User(
            email="existing@example.com",
            username="existinguser",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(existing_user)
        await db_session.commit()

        # Try to register with same email
        user_data = {
            "email": "existing@example.com",
            "username": "newusername",
            "full_name": "Another User",
            "password": "password123"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 409
        data = response.json()
        assert "email" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, db_session: AsyncSession):
        """Test registration with duplicate username"""
        # Create existing user
        existing_user = User(
            email="existing2@example.com",
            username="takenusername",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(existing_user)
        await db_session.commit()

        # Try to register with same username
        user_data = {
            "email": "newemail@example.com",
            "username": "takenusername",
            "full_name": "Another User",
            "password": "password123"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 409
        data = response.json()
        assert "username" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email"""
        user_data = {
            "email": "not-an-email",
            "username": "validuser",
            "full_name": "Valid User",
            "password": "password123"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with password too short"""
        user_data = {
            "email": "user@example.com",
            "username": "validuser",
            "full_name": "Valid User",
            "password": "short"  # Less than 8 characters
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_username(self, client: AsyncClient):
        """Test registration with username too short"""
        user_data = {
            "email": "user@example.com",
            "username": "ab",  # Less than 3 characters
            "full_name": "Valid User",
            "password": "password123"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint"""

    @pytest.mark.asyncio
    async def test_login_with_email_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login with email"""
        # Create test user
        user = User(
            email="logintest@example.com",
            username="loginuser",
            hashed_password=get_password_hash("testpass123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Login with email
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "logintest@example.com",
                "password": "testpass123",
                "remember_me": "false"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify tokens are set in cookies
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_with_username_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login with username"""
        # Create test user
        user = User(
            email="logintest2@example.com",
            username="loginuser2",
            hashed_password=get_password_hash("testpass123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Login with username
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "loginuser2",
                "password": "testpass123",
                "remember_me": "false"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with wrong password"""
        # Create test user
        user = User(
            email="wrongpass@example.com",
            username="wrongpassuser",
            hashed_password=get_password_hash("correctpass"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Try login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "wrongpass@example.com",
                "password": "wrongpassword",
                "remember_me": "false"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "credentials" in data["detail"].lower() or "invalid" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "doesnotexist@example.com",
                "password": "somepassword",
                "remember_me": "false"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with inactive user account"""
        # Create inactive user
        user = User(
            email="inactive@example.com",
            username="inactiveuser",
            hashed_password=get_password_hash("password123"),
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()

        # Try to login
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "inactive@example.com",
                "password": "password123",
                "remember_me": "false"
            }
        )

        assert response.status_code == 403
        data = response.json()
        assert "inactive" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_remember_me_true(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with remember_me enabled"""
        # Create test user
        user = User(
            email="remember@example.com",
            username="rememberuser",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Login with remember_me
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "remember@example.com",
                "password": "password123",
                "remember_me": "true"
            }
        )

        assert response.status_code == 200

        # Verify cookies have max_age set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies


class TestTokenRefresh:
    """Test token refresh endpoint"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful token refresh"""
        # Create test user
        user = User(
            email="refresh@example.com",
            username="refreshuser",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create refresh token
        refresh_token = create_refresh_token(subject=str(user.id))

        # Refresh the token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != refresh_token  # New token should be different

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token"""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, client: AsyncClient, db_session: AsyncSession):
        """Test refresh with expired token"""
        # Create test user
        user = User(
            email="expired@example.com",
            username="expireduser",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create expired refresh token (negative expiry)
        expired_token = create_refresh_token(
            subject=str(user.id),
            expires_delta=timedelta(seconds=-1)
        )

        # Try to refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_access_token(self, client: AsyncClient, db_session: AsyncSession):
        """Test refresh using access token instead of refresh token (should fail)"""
        # Create test user
        user = User(
            email="wrongtoken@example.com",
            username="wrongtokenuser",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create access token (wrong type)
        access_token = create_access_token(subject=str(user.id))

        # Try to refresh with access token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}
        )

        # Should fail because token type is wrong
        assert response.status_code == 401


class TestLogout:
    """Test logout endpoint"""

    @pytest.mark.asyncio
    async def test_logout_success(self, authenticated_client: tuple):
        """Test successful logout"""
        client, user_data = authenticated_client

        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "logged out" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_logout_without_auth(self, client: AsyncClient):
        """Test logout without authentication"""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401


class TestGetCurrentUser:
    """Test get current user endpoint"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, authenticated_client: tuple):
        """Test getting current user info"""
        client, user_data = authenticated_client

        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_without_auth(self, client: AsyncClient):
        """Test getting current user without authentication"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token"""
        client.headers["Authorization"] = "Bearer invalid.token.here"

        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
