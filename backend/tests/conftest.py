"""
Pytest configuration and fixtures
"""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.core.config import settings
from app.main import app
from app.api.dependencies import get_db

# Test database URL
# Use in-memory SQLite for testing if no DATABASE_URL is configured
if settings.DATABASE_URL:
    TEST_DATABASE_URL = settings.DATABASE_URL.unicode_string().replace(
        settings.POSTGRES_DB,
        f"{settings.POSTGRES_DB}_test"
    )
else:
    # Fallback to SQLite for testing
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Create test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Get test database session."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Get test client with overridden database dependency."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(
    client: AsyncClient, 
    db_session: AsyncSession
) -> AsyncGenerator[tuple[AsyncClient, dict], None]:
    """Get authenticated test client with user data."""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    # Create test user
    user = User(
        email="auth_test@example.com",
        username="auth_test_user",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Auth Test User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "auth_test@example.com",
            "password": "testpassword123",
        }
    )
    tokens = response.json()
    
    # Add auth header to client
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    
    user_data = {
        "user": user,
        "tokens": tokens,
        "email": "auth_test@example.com",
        "password": "testpassword123"
    }
    
    yield client, user_data