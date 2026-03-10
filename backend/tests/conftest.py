"""
Pytest configuration and fixtures
"""

from typing import Generator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.core.config import settings
from app.main import app
from app.api.dependencies import get_db

# Test database URL — use TEST_DATABASE_URL env var, or fall back to app's DATABASE_URL with _test suffix
import os

_test_db_url = os.getenv("TEST_DATABASE_URL")
if not _test_db_url:
    _base_url = settings.DATABASE_URL_SQLALCHEMY
    if "postgresql" in _base_url and settings.POSTGRES_DB:
        _test_db_url = _base_url.replace(settings.POSTGRES_DB, f"{settings.POSTGRES_DB}_test")
    else:
        _test_db_url = _base_url

TEST_DATABASE_URL = _test_db_url

# Create sync test engine (matches app's sync architecture)
test_engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create test database tables."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(setup_database) -> Generator[Session, None, None]:
    """Get test database session."""
    session = TestSessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
async def client(db_session: Session) -> AsyncClient:
    """Get test client with overridden database dependency."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient, db_session: Session):
    """Get authenticated test client with user data."""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        email="auth_test@example.com",
        username="auth_test_user",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Auth Test User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "auth_test@example.com",
            "password": "testpassword123",
        },
    )
    tokens = response.json()

    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    user_data = {
        "user": user,
        "tokens": tokens,
        "email": "auth_test@example.com",
        "password": "testpassword123",
    }

    yield client, user_data
