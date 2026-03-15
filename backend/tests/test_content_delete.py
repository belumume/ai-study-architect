"""
Tests for content deletion with confirm_delete cascade behavior.
"""

import uuid

import pytest

from app.models.concept import Concept
from app.models.content import Content
from app.models.user_concept_mastery import UserConceptMastery


@pytest.fixture
def content_with_concepts(db_session, authenticated_client):
    """Create content with concepts and mastery records for cascade testing."""
    _, user_data = authenticated_client
    user = user_data["user"]

    content = Content(
        user_id=user.id,
        title="Test Content With Concepts",
        content_type="document",
        processing_status="completed",
        extracted_text="Test text for deletion testing.",
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)

    concepts = []
    for i in range(3):
        concept = Concept(
            name=f"Test Concept {i}",
            description=f"Description for concept {i}",
            concept_type="definition",
            difficulty="beginner",
            content_id=content.id,
        )
        db_session.add(concept)
        concepts.append(concept)
    db_session.commit()
    for c in concepts:
        db_session.refresh(c)

    mastery_records = []
    for concept in concepts[:2]:
        mastery = UserConceptMastery(
            user_id=user.id,
            concept_id=concept.id,
            status="learning",
            mastery_level=0.3,
        )
        db_session.add(mastery)
        mastery_records.append(mastery)
    db_session.commit()

    return content, concepts, mastery_records


@pytest.fixture
def content_without_concepts(db_session, authenticated_client):
    """Create content with no concepts for simple deletion testing."""
    _, user_data = authenticated_client
    user = user_data["user"]

    content = Content(
        user_id=user.id,
        title="Simple Content",
        content_type="document",
        processing_status="completed",
        extracted_text="Simple text no concepts.",
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    return content


class TestConfirmDeleteCascade:
    @pytest.mark.asyncio
    async def test_delete_with_concepts_returns_409(
        self, authenticated_client, content_with_concepts
    ):
        """DELETE content with concepts returns 409 with impact counts."""
        client, _ = authenticated_client
        content, concepts, mastery_records = content_with_concepts

        response = await client.delete(f"/api/v1/content/{content.id}")
        assert response.status_code == 409

        detail = response.json()["detail"]
        assert detail["concepts_count"] == 3
        assert detail["mastery_records"] == 2
        assert "confirm_delete=true" in detail["message"]

    @pytest.mark.asyncio
    async def test_delete_with_confirm_cascades(
        self, authenticated_client, content_with_concepts, db_session
    ):
        """DELETE with confirm_delete=true cascades and removes all records."""
        client, _ = authenticated_client
        content, concepts, mastery_records = content_with_concepts

        # Capture IDs before deletion (ORM objects expire after cascade)
        content_id = content.id
        concept_ids = [c.id for c in concepts]

        response = await client.delete(f"/api/v1/content/{content_id}?confirm_delete=true")
        assert response.status_code == 204

        # Verify concepts are deleted (CASCADE from content FK)
        remaining = db_session.query(Concept).filter(Concept.content_id == content_id).count()
        assert remaining == 0

        # Verify mastery records are deleted (CASCADE from concept FK)
        remaining_mastery = (
            db_session.query(UserConceptMastery)
            .filter(UserConceptMastery.concept_id.in_(concept_ids))
            .count()
        )
        assert remaining_mastery == 0

    @pytest.mark.asyncio
    async def test_delete_without_concepts_succeeds(
        self, authenticated_client, content_without_concepts
    ):
        """DELETE content with no concepts succeeds without confirmation."""
        client, _ = authenticated_client
        content = content_without_concepts

        response = await client.delete(f"/api/v1/content/{content.id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_409_response_structure(self, authenticated_client, content_with_concepts):
        """409 response has correct structure with message, counts, and records."""
        client, _ = authenticated_client
        content, _, _ = content_with_concepts

        response = await client.delete(f"/api/v1/content/{content.id}")
        assert response.status_code == 409

        detail = response.json()["detail"]
        assert "message" in detail
        assert "concepts_count" in detail
        assert "mastery_records" in detail
        assert isinstance(detail["concepts_count"], int)
        assert isinstance(detail["mastery_records"], int)
