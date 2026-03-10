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
from app.main import app as fastapi_app
from app.api.dependencies import get_db

# Import all models so SQLAlchemy can resolve relationship string references
from app.models.user import User as _User  # noqa: F401
from app.models.content import Content as _Content  # noqa: F401
from app.models.study_session import StudySession as _StudySession  # noqa: F401
from app.models.practice import PracticeSession as _Practice  # noqa: F401
from app.models.chat_message import ChatMessage as _ChatMessage  # noqa: F401
from app.models.concept import Concept as _Concept  # noqa: F401

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

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Disable rate limiting for tests
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    disabled_limiter = Limiter(key_func=get_remote_address, enabled=False)
    fastapi_app.state.limiter = disabled_limiter
    # Also patch module-level limiters in route files
    import app.api.v1.auth as auth_module
    auth_module.limiter = disabled_limiter
    import app.main as main_module
    main_module.limiter = disabled_limiter

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as c:
        yield c

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient, db_session: Session):
    """Get authenticated test client with user data."""
    import uuid
    from app.models.user import User
    from app.core.security import get_password_hash

    # Use unique email/username per fixture invocation to prevent UniqueViolation
    unique_id = uuid.uuid4().hex[:8]
    email = f"auth_test_{unique_id}@example.com"
    username = f"auth_test_{unique_id}"

    user = User(
        email=email,
        username=username,
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
        data={
            "username": email,
            "password": "testpassword123",
            "remember_me": "false",
        },
    )
    tokens = response.json()

    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    user_data = {
        "user": user,
        "tokens": tokens,
        "email": email,
        "password": "testpassword123",
    }

    yield client, user_data

    # Cleanup
    try:
        db_session.delete(user)
        db_session.commit()
    except Exception:
        db_session.rollback()
