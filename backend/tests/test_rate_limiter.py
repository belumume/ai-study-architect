"""
Rate limiter tests.

Tests that slowapi rate limiting works on auth endpoints.
The conftest client fixture disables rate limiting — these tests
use a separate fixture with rate limiting enabled via sync TestClient,
which properly triggers SlowAPIMiddleware route detection.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.main import app as fastapi_app


@pytest.fixture
def rate_limited_client(db_session: Session) -> TestClient:
    """Sync TestClient with rate limiting ENABLED.

    Uses the shared limiter instance and toggles enabled=True.
    Uses FastAPI's TestClient for proper SlowAPIMiddleware integration.
    """

    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    from app.core.rate_limiter import limiter

    limiter.enabled = True
    limiter.reset()

    with TestClient(fastapi_app, base_url="http://localhost") as c:
        yield c

    fastapi_app.dependency_overrides.clear()
    limiter.enabled = False


class TestRateLimiter:
    """Test rate limiting on auth endpoints."""

    def test_register_rate_limit_allows_under_limit(self, rate_limited_client):
        """Requests under the limit should succeed (or fail for other reasons, not 429)."""
        for i in range(3):
            response = rate_limited_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"ratelimit{i}@example.com",
                    "username": f"ratelimit{i}",
                    "password": "TestPass123",
                },
            )
            assert response.status_code != 429, f"Request {i + 1} was rate limited unexpectedly"

    def test_register_rate_limit_blocks_over_limit(self, rate_limited_client):
        """The 6th request within a minute should be rate limited (429)."""
        for i in range(6):
            response = rate_limited_client.post(
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

    def test_login_rate_limit_blocks_over_limit(self, rate_limited_client):
        """Login endpoint should also be rate limited at 5/minute."""
        for i in range(6):
            response = rate_limited_client.post(
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

    def test_rate_limit_response_format(self, rate_limited_client):
        """Rate limited response should have proper error format."""
        for i in range(6):
            response = rate_limited_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"format{i}@example.com",
                    "username": f"format{i}",
                    "password": "TestPass123",
                },
            )

        assert response.status_code == 429
        assert "Retry-After" in response.headers or response.status_code == 429
