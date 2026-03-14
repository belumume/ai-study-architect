"""
Tests for the concept extraction service.

Tests pure functions (normalization, validation) directly.
Tests service logic with mocked Claude API responses.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models.content import Content
from app.models.subject import Subject
from app.models.user import User
from app.services.concept_extraction import (
    ConceptExtractionService,
    ExtractionError,
    normalize_concept_name,
)

# ============================================================================
# Pure function tests — no mocking needed
# ============================================================================


class TestNormalizeConceptName:
    def test_basic_lowercase(self):
        assert normalize_concept_name("Binary Search") == "binary search"

    def test_collapse_whitespace(self):
        assert normalize_concept_name("binary  search   algorithm") == "binary search algorithm"

    def test_strip_articles(self):
        assert (
            normalize_concept_name("Define the stack data structure")
            == "define stack data structure"
        )

    def test_strip_prepositions(self):
        assert (
            normalize_concept_name("Implement binary search in an array")
            == "implement binary search array"
        )

    def test_empty_after_stripping(self):
        assert normalize_concept_name("the a an") == ""

    def test_leading_trailing_whitespace(self):
        assert normalize_concept_name("  Calculate derivative  ") == "calculate derivative"

    def test_vs_stripped(self):
        assert normalize_concept_name("stack vs queue") == "stack queue"


class TestValidateConcepts:
    def setup_method(self):
        self.service = ConceptExtractionService()

    def test_valid_concept_passes(self):
        parsed = {
            "concepts": [
                {
                    "name": "Define binary search",
                    "description": "A search algorithm that finds elements in sorted arrays.",
                    "concept_type": "definition",
                    "difficulty": "beginner",
                    "estimated_minutes": 15,
                    "keywords": ["search", "binary", "sorted"],
                    "examples": ["Find 7 in [1,3,5,7,9]"],
                }
            ]
        }
        result = self.service._validate_concepts(parsed)
        assert len(result["concepts"]) == 1

    def test_invalid_concept_type_filtered(self):
        parsed = {
            "concepts": [
                {
                    "name": "Test concept",
                    "description": "A test.",
                    "concept_type": "INVALID_TYPE",
                    "difficulty": "beginner",
                    "estimated_minutes": 15,
                    "keywords": [],
                    "examples": [],
                }
            ]
        }
        result = self.service._validate_concepts(parsed)
        assert len(result["concepts"]) == 0

    def test_missing_required_field_filtered(self):
        parsed = {
            "concepts": [
                {
                    "name": "Test concept",
                    "concept_type": "definition",
                    "difficulty": "beginner",
                    "estimated_minutes": 15,
                    "keywords": [],
                    "examples": [],
                }
            ]
        }
        result = self.service._validate_concepts(parsed)
        assert len(result["concepts"]) == 0

    def test_empty_concepts_list(self):
        parsed = {"concepts": []}
        result = self.service._validate_concepts(parsed)
        assert len(result["concepts"]) == 0

    def test_mixed_valid_and_invalid(self):
        parsed = {
            "concepts": [
                {
                    "name": "Valid concept",
                    "description": "This is valid.",
                    "concept_type": "definition",
                    "difficulty": "beginner",
                    "estimated_minutes": 10,
                    "keywords": ["test"],
                    "examples": ["Q1"],
                },
                {
                    "name": "",
                    "description": "Invalid.",
                    "concept_type": "definition",
                    "difficulty": "beginner",
                    "estimated_minutes": 10,
                    "keywords": [],
                    "examples": [],
                },
            ]
        }
        result = self.service._validate_concepts(parsed)
        assert len(result["concepts"]) == 1
        assert result["concepts"][0]["name"] == "Valid concept"


# ============================================================================
# Service tests — mock at _call_claude level (not HTTP transport)
# ============================================================================

VALID_CLAUDE_RESPONSE = {
    "concepts": [
        {
            "name": "Define binary search algorithm",
            "description": "A search algorithm that finds elements in sorted arrays.",
            "concept_type": "definition",
            "difficulty": "beginner",
            "estimated_minutes": 15,
            "keywords": ["binary search", "search", "algorithm", "sorted array"],
            "examples": ["Given sorted array [1,3,5,7,9], find element 7"],
        },
        {
            "name": "Implement binary search on sorted array",
            "description": "Write code to perform binary search with O(log n) complexity.",
            "concept_type": "procedure",
            "difficulty": "intermediate",
            "estimated_minutes": 25,
            "keywords": ["implementation", "binary search", "O(log n)"],
            "examples": ["Implement binary_search(arr, target) returning the index"],
        },
    ],
    "dependencies": [],
    "metadata": {
        "total_extracted": 2,
        "extraction_confidence": 0.9,
        "notes": "Clear algorithmic content",
    },
}


@pytest.fixture
def test_data(db_session):
    """Create user, subject, content for FK-valid extraction tests."""
    from app.core.security import get_password_hash

    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"extract_{uid}@test.com",
        username=f"extract_{uid}",
        hashed_password=get_password_hash("test123"),
        full_name="Test",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    subject = Subject(user_id=user.id, name=f"Test Subject {uid}", color="#D4FF00")
    db_session.add(subject)
    db_session.flush()

    content = Content(
        user_id=user.id,
        title="Test Content",
        content_type="document",
        processing_status="completed",
        extracted_text="Binary search is an efficient algorithm. " * 20,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(subject)
    db_session.refresh(content)

    return {"user": user, "subject": subject, "content": content}


class TestExtractionService:
    def setup_method(self):
        self.service = ConceptExtractionService()

    @pytest.mark.asyncio
    async def test_extract_concepts_happy_path(self, db_session, test_data):
        mock_call = AsyncMock(return_value=VALID_CLAUDE_RESPONSE)

        with (
            patch.object(self.service, "_call_claude", mock_call),
            patch("app.services.concept_extraction.claude_service") as mock_cs,
        ):
            mock_cs.api_key = "test-key"
            result = await self.service.extract_concepts(
                test_data["content"].id,
                test_data["subject"].id,
                test_data["content"].extracted_text,
                test_data["user"].id,
                db_session,
            )

        assert result.created_concepts == 2
        assert result.chunks_succeeded >= 1
        assert result.chunks_failed == 0

    @pytest.mark.asyncio
    async def test_deduplication_across_chunks(self, db_session, test_data):
        """Same concept name in multiple chunks should be deduplicated."""
        long_text = "Binary search algorithm explanation. " * 200
        mock_call = AsyncMock(return_value=VALID_CLAUDE_RESPONSE)

        with (
            patch.object(self.service, "_call_claude", mock_call),
            patch("app.services.concept_extraction.claude_service") as mock_cs,
        ):
            mock_cs.api_key = "test-key"
            result = await self.service.extract_concepts(
                test_data["content"].id,
                test_data["subject"].id,
                long_text,
                test_data["user"].id,
                db_session,
            )

        # Even with multiple chunks returning same concepts, dedup prevents duplicates
        assert result.created_concepts == 2

    @pytest.mark.asyncio
    async def test_empty_text_raises_error(self, db_session, test_data):
        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            with pytest.raises(ExtractionError, match="No text chunks"):
                await self.service.extract_concepts(
                    test_data["content"].id,
                    test_data["subject"].id,
                    "",
                    test_data["user"].id,
                    db_session,
                )

    @pytest.mark.asyncio
    async def test_all_chunks_fail_raises_error(self, db_session, test_data):
        mock_call = AsyncMock(side_effect=Exception("API error"))

        with (
            patch.object(self.service, "_call_claude", mock_call),
            patch("app.services.concept_extraction.claude_service") as mock_cs,
        ):
            mock_cs.api_key = "test-key"
            with pytest.raises(ExtractionError, match="All .* chunks failed"):
                await self.service.extract_concepts(
                    test_data["content"].id,
                    test_data["subject"].id,
                    "Some content to extract from. " * 20,
                    test_data["user"].id,
                    db_session,
                )

    @pytest.mark.asyncio
    async def test_partial_failure_returns_results(self, db_session, test_data):
        """If some chunks fail, the successful ones should still produce concepts."""
        long_text = "Content for extraction. " * 200
        call_count = 0

        async def alternating(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise Exception("Simulated failure")
            return VALID_CLAUDE_RESPONSE

        with (
            patch.object(self.service, "_call_claude", side_effect=alternating),
            patch("app.services.concept_extraction.claude_service") as mock_cs,
        ):
            mock_cs.api_key = "test-key"
            result = await self.service.extract_concepts(
                test_data["content"].id,
                test_data["subject"].id,
                long_text,
                test_data["user"].id,
                db_session,
            )

        assert result.created_concepts > 0
        assert result.chunks_failed > 0
        assert result.chunks_succeeded > 0

    @pytest.mark.asyncio
    async def test_no_api_key_raises_error(self, db_session, test_data):
        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = None
            with pytest.raises(ExtractionError, match="API key not configured"):
                await self.service.extract_concepts(
                    test_data["content"].id,
                    test_data["subject"].id,
                    "Some text",
                    test_data["user"].id,
                    db_session,
                )

    @pytest.mark.asyncio
    async def test_text_length_cap(self, db_session, test_data):
        """Text exceeding MAX_TEXT_LENGTH should be truncated, not rejected."""
        long_text = "x" * 200_000
        mock_call = AsyncMock(return_value=VALID_CLAUDE_RESPONSE)

        with (
            patch.object(self.service, "_call_claude", mock_call),
            patch("app.services.concept_extraction.claude_service") as mock_cs,
        ):
            mock_cs.api_key = "test-key"
            result = await self.service.extract_concepts(
                test_data["content"].id,
                test_data["subject"].id,
                long_text,
                test_data["user"].id,
                db_session,
            )

        assert result.created_concepts >= 0
