"""Test utilities and helper functions"""

from datetime import datetime
from typing import Dict
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User
from app.core.security import get_password_hash


def create_test_user(
    db: Session,
    email: str = None,
    username: str = None,
    password: str = "password123",
    is_active: bool = True,
    is_verified: bool = True
) -> User:
    """Create a test user in the database"""
    if not email:
        email = f"test_{uuid4().hex[:8]}@example.com"
    if not username:
        username = f"test_user_{uuid4().hex[:8]}"
    
    user = User(
        id=uuid4(),
        email=email,
        username=username,
        full_name="Test User",
        hashed_password=get_password_hash(password),
        is_active=is_active,
        is_verified=is_verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(client: TestClient, username: str, password: str) -> Dict[str, str]:
    """Get authentication headers for a user"""
    # Login to get token
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": username,
            "password": password
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}