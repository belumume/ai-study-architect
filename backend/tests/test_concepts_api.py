"""
Tests for concept extraction and subject detail API endpoints.
"""

import uuid

import pytest

from app.models.content import Content
from app.models.subject import Subject


@pytest.fixture
def subject_and_content(db_session, authenticated_client):
    """Create a subject and content item for testing."""
    _, user_data = authenticated_client
    user = user_data["user"]

    subject = Subject(
        user_id=user.id,
        name="Test Subject",
        color="#D4FF00",
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)

    content = Content(
        user_id=user.id,
        title="Test Content",
        content_type="document",
        processing_status="completed",
        extracted_text="Binary search is an efficient algorithm. " * 20,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    return subject, content


class TestExtractEndpoint:
    @pytest.mark.asyncio
    async def test_extract_requires_auth(self, client):
        response = await client.post(
            "/api/v1/concepts/extract",
            json={
                "content_id": str(uuid.uuid4()),
                "subject_id": str(uuid.uuid4()),
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_extract_content_not_found(self, authenticated_client):
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/concepts/extract",
            json={
                "content_id": str(uuid.uuid4()),
                "subject_id": str(uuid.uuid4()),
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_extract_subject_not_found(self, authenticated_client, db_session):
        client, user_data = authenticated_client
        user = user_data["user"]

        content = Content(
            user_id=user.id,
            title="Test",
            content_type="document",
            processing_status="completed",
            extracted_text="Some text here.",
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)

        response = await client.post(
            "/api/v1/concepts/extract",
            json={
                "content_id": str(content.id),
                "subject_id": str(uuid.uuid4()),
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_extract_content_not_processed(self, authenticated_client, db_session):
        client, user_data = authenticated_client
        user = user_data["user"]

        subject = Subject(user_id=user.id, name="Sub", color="#D4FF00")
        db_session.add(subject)

        content = Content(
            user_id=user.id,
            title="Pending",
            content_type="document",
            processing_status="pending",
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(subject)
        db_session.refresh(content)

        response = await client.post(
            "/api/v1/concepts/extract",
            json={
                "content_id": str(content.id),
                "subject_id": str(subject.id),
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_extract_concurrency_guard(
        self, authenticated_client, db_session, subject_and_content
    ):
        client, _ = authenticated_client
        subject, content = subject_and_content

        content.extraction_status = "extracting"
        db_session.commit()

        response = await client.post(
            "/api/v1/concepts/extract",
            json={
                "content_id": str(content.id),
                "subject_id": str(subject.id),
            },
        )
        assert response.status_code == 409


class TestSubjectDetailEndpoint:
    @pytest.mark.asyncio
    async def test_detail_requires_auth(self, client):
        response = await client.get(f"/api/v1/concepts/subjects/{uuid.uuid4()}/detail")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_detail_subject_not_found(self, authenticated_client):
        client, _ = authenticated_client
        response = await client.get(f"/api/v1/concepts/subjects/{uuid.uuid4()}/detail")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_detail_empty_subject(self, authenticated_client, db_session):
        client, user_data = authenticated_client
        user = user_data["user"]

        subject = Subject(user_id=user.id, name="Empty Subject", color="#00F2FE")
        db_session.add(subject)
        db_session.commit()
        db_session.refresh(subject)

        response = await client.get(f"/api/v1/concepts/subjects/{subject.id}/detail")
        assert response.status_code == 200
        data = response.json()
        assert data["subject"]["name"] == "Empty Subject"
        assert data["concepts"] == []
        assert data["mastery_summary"]["total_concepts"] == 0
        assert data["mastery_summary"]["mastery_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_detail_cross_user_isolation(self, client, db_session):
        """Another user's subject should return 404, not their data."""
        from app.core.security import get_password_hash
        from app.models.user import User

        uid = uuid.uuid4().hex[:8]
        other_user = User(
            email=f"other_{uid}@test.com",
            username=f"other_{uid}",
            hashed_password=get_password_hash("pass123"),
            full_name="Other",
            is_active=True,
            is_verified=True,
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_subject = Subject(user_id=other_user.id, name="Private", color="#FF2D7B")
        db_session.add(other_subject)
        db_session.commit()
        db_session.refresh(other_subject)

        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": f"other_{uid}@test.com", "password": "pass123"},
        )

        uid2 = uuid.uuid4().hex[:8]
        attacker = User(
            email=f"attacker_{uid2}@test.com",
            username=f"attacker_{uid2}",
            hashed_password=get_password_hash("pass123"),
            full_name="Attacker",
            is_active=True,
            is_verified=True,
        )
        db_session.add(attacker)
        db_session.commit()

        login_resp = await client.post(
            "/api/v1/auth/login",
            data={
                "username": f"attacker_{uid2}@test.com",
                "password": "pass123",
                "remember_me": "true",
            },
        )
        assert login_resp.status_code == 200
        access_token = login_resp.cookies.get("access_token")
        assert access_token, "Attacker login did not set access_token cookie"
        client.headers["Authorization"] = f"Bearer {access_token}"

        response = await client.get(f"/api/v1/concepts/subjects/{other_subject.id}/detail")
        assert response.status_code == 404
