"""
Integration tests for the concept extraction service.

Unlike the unit tests in test_concept_extraction.py (which mock _call_claude),
these tests mock at the HTTP transport level (httpx) and let ALL service logic
run for real: chunking, normalization, validation, deduplication, and DB inserts.

This verifies the full extraction pipeline end-to-end with controlled API responses.
"""

import json
import uuid
from unittest.mock import patch

import httpx
import pytest

from app.core.security import get_password_hash
from app.models.concept import Concept
from app.models.content import Content
from app.models.subject import Subject
from app.models.user import User
from app.models.user_concept_mastery import UserConceptMastery
from app.services.concept_extraction import (
    ConceptExtractionService,
    ExtractionError,
    normalize_concept_name,
)

# ============================================================================
# Helpers
# ============================================================================


def _claude_api_response(concepts: list[dict], dependencies: list[dict] | None = None) -> dict:
    """Build a full Claude API HTTP response body wrapping extracted concepts."""
    payload = {
        "concepts": concepts,
        "dependencies": dependencies or [],
        "metadata": {
            "total_extracted": len(concepts),
            "extraction_confidence": 0.85,
            "notes": "Test extraction",
        },
    }
    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": json.dumps(payload)}],
        "model": "claude-haiku-4-5",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 100, "output_tokens": 200},
    }


CONCEPT_BINARY_SEARCH = {
    "name": "Implement binary search on sorted array",
    "description": "Write code to perform binary search with O(log n) time complexity.",
    "concept_type": "procedure",
    "difficulty": "intermediate",
    "estimated_minutes": 25,
    "keywords": ["binary search", "sorted array", "O(log n)"],
    "examples": ["Implement binary_search(arr, target) returning the index"],
}

CONCEPT_LINKED_LIST = {
    "name": "Define singly linked list structure",
    "description": "A linear data structure where elements point to the next node.",
    "concept_type": "definition",
    "difficulty": "beginner",
    "estimated_minutes": 15,
    "keywords": ["linked list", "node", "pointer"],
    "examples": ["Draw a singly linked list with 3 nodes"],
}

CONCEPT_STACK = {
    "name": "Implement stack using array",
    "description": "Use an array to implement push, pop, and peek operations.",
    "concept_type": "procedure",
    "difficulty": "beginner",
    "estimated_minutes": 20,
    "keywords": ["stack", "LIFO", "push", "pop"],
    "examples": ["Implement a stack class with push() and pop()"],
}


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def extraction_data(db_session):
    """Create user, subject, and content for extraction integration tests."""
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"integ_{uid}@test.com",
        username=f"integ_{uid}",
        hashed_password=get_password_hash("test123"),
        full_name="Integration Test",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    subject = Subject(user_id=user.id, name=f"Data Structures {uid}", color="#D4FF00")
    db_session.add(subject)
    db_session.flush()

    content = Content(
        user_id=user.id,
        title="DS Lecture Notes",
        content_type="document",
        processing_status="completed",
        extracted_text=(
            "Binary search is an efficient algorithm for finding elements in sorted arrays. "
            "It works by repeatedly dividing the search interval in half. "
            "The time complexity is O(log n) which makes it much faster than linear search. "
            "A linked list is a linear data structure where each element points to the next. "
            "Stacks follow the Last-In-First-Out (LIFO) principle. "
        )
        * 10,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(subject)
    db_session.refresh(content)

    return {"user": user, "subject": subject, "content": content}


@pytest.fixture
def service():
    return ConceptExtractionService()


def _mock_transport(response_body: dict, status_code: int = 200):
    """Create a mock httpx transport that returns the given response."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            json=response_body,
            request=request,
        )

    return httpx.MockTransport(handler)


def _patched_async_client(transport):
    """Return a factory that creates real httpx.AsyncClient with mocked transport.

    The service code does `async with httpx.AsyncClient(timeout=...) as client:`.
    We replace the class with a factory that ignores the original kwargs and injects
    our transport, but still returns a real AsyncClient (so .post(), .json(), etc. work).
    """
    _real_cls = httpx.AsyncClient

    def factory(**_kwargs):
        return _real_cls(transport=transport)

    return factory


# ============================================================================
# Pipeline integration tests — mock at HTTP level, real service logic
# ============================================================================


class TestExtractionPipelineIntegration:
    """End-to-end pipeline: normalize -> chunk -> extract -> validate -> dedup -> insert."""

    @pytest.mark.asyncio
    async def test_full_pipeline_produces_valid_concepts(
        self, db_session, extraction_data, service
    ):
        """Full pipeline: text -> chunks -> Claude API -> validate -> dedup -> DB insert."""
        api_response = _claude_api_response([CONCEPT_BINARY_SEARCH, CONCEPT_LINKED_LIST])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 2
        assert len(result.concept_ids) == 2
        assert result.chunks_succeeded >= 1
        assert result.chunks_failed == 0
        assert result.message is None

        concepts = (
            db_session.query(Concept)
            .filter(Concept.subject_id == extraction_data["subject"].id)
            .all()
        )
        assert len(concepts) == 2

        names = {c.name for c in concepts}
        assert "Implement binary search on sorted array" in names
        assert "Define singly linked list structure" in names

        for concept in concepts:
            assert concept.content_id == extraction_data["content"].id
            assert concept.subject_id == extraction_data["subject"].id
            assert concept.concept_type in ("procedure", "definition")
            assert concept.difficulty in ("beginner", "intermediate")
            assert concept.estimated_minutes > 0
            assert concept.keywords is not None

        mastery_records = (
            db_session.query(UserConceptMastery)
            .filter(UserConceptMastery.user_id == extraction_data["user"].id)
            .all()
        )
        assert len(mastery_records) == 2
        for m in mastery_records:
            assert m.status == "not_started"
            assert m.mastery_level == 0.0

    @pytest.mark.asyncio
    async def test_pipeline_with_three_concepts(self, db_session, extraction_data, service):
        """Pipeline correctly inserts 3 distinct concepts with correct metadata."""
        api_response = _claude_api_response(
            [CONCEPT_BINARY_SEARCH, CONCEPT_LINKED_LIST, CONCEPT_STACK]
        )
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 3
        assert result.chunks_total >= 1


# ============================================================================
# Deduplication integration tests
# ============================================================================


class TestDeduplicationIntegration:
    """Test that dedup works across chunks with real normalization logic."""

    @pytest.mark.asyncio
    async def test_duplicate_concepts_across_chunks_deduplicated(
        self, db_session, extraction_data, service
    ):
        """Same concept name from different chunks should produce only one DB record."""
        duplicate_concept = {
            "name": "Implement binary search on sorted array",
            "description": "A different description but same concept name.",
            "concept_type": "procedure",
            "difficulty": "advanced",
            "estimated_minutes": 30,
            "keywords": ["binary", "search"],
            "examples": ["Another example"],
        }
        api_response = _claude_api_response([CONCEPT_BINARY_SEARCH, duplicate_concept])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 1

    @pytest.mark.asyncio
    async def test_normalization_deduplicates_variant_names(
        self, db_session, extraction_data, service
    ):
        """Concepts with different casing/articles but same normalized form are deduplicated."""
        variant_concept = {
            "name": "Implement the Binary Search on a Sorted Array",
            "description": "Same concept, different casing and articles.",
            "concept_type": "procedure",
            "difficulty": "intermediate",
            "estimated_minutes": 25,
            "keywords": ["binary search"],
            "examples": ["Example"],
        }
        api_response = _claude_api_response([CONCEPT_BINARY_SEARCH, variant_concept])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        normalized_original = normalize_concept_name(CONCEPT_BINARY_SEARCH["name"])
        normalized_variant = normalize_concept_name(variant_concept["name"])
        assert normalized_original == normalized_variant
        assert result.created_concepts == 1

    @pytest.mark.asyncio
    async def test_truly_different_concepts_not_deduplicated(
        self, db_session, extraction_data, service
    ):
        """Concepts with genuinely different names should NOT be collapsed."""
        api_response = _claude_api_response(
            [CONCEPT_BINARY_SEARCH, CONCEPT_LINKED_LIST, CONCEPT_STACK]
        )
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 3


# ============================================================================
# Chunking edge cases — real content_processor.extract_chunks runs
# ============================================================================


class TestChunkingEdgeCases:
    """Test chunking edge cases with real extract_chunks logic."""

    @pytest.mark.asyncio
    async def test_empty_content_raises_extraction_error(
        self, db_session, extraction_data, service
    ):
        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            with pytest.raises(ExtractionError, match="No text chunks"):
                await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    "",
                    extraction_data["user"].id,
                    db_session,
                )

    @pytest.mark.asyncio
    async def test_whitespace_only_content_raises_extraction_error(
        self, db_session, extraction_data, service
    ):
        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            with pytest.raises(ExtractionError, match="No text chunks"):
                await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    "     \n\n\t\t   \n   ",
                    extraction_data["user"].id,
                    db_session,
                )

    @pytest.mark.asyncio
    async def test_very_short_content_produces_single_chunk(
        self, db_session, extraction_data, service
    ):
        """Content shorter than chunk_size should produce exactly one chunk."""
        short_text = "Binary search finds elements in sorted arrays in O(log n) time."
        api_response = _claude_api_response([CONCEPT_BINARY_SEARCH])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    short_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.chunks_total == 1
        assert result.chunks_succeeded == 1
        assert result.created_concepts == 1

    @pytest.mark.asyncio
    async def test_text_exceeding_max_length_is_truncated(
        self, db_session, extraction_data, service
    ):
        """Text beyond MAX_TEXT_LENGTH should be silently truncated, not rejected."""
        huge_text = "Data structures are fundamental. " * 10_000  # ~320k chars
        api_response = _claude_api_response([CONCEPT_BINARY_SEARCH])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    huge_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts >= 1
        assert result.chunks_total <= service.MAX_CHUNKS


# ============================================================================
# Malformed Claude response handling
# ============================================================================


class TestMalformedResponseHandling:
    """Test that malformed Claude API responses are handled gracefully."""

    @pytest.mark.asyncio
    async def test_missing_required_fields_filtered_out(self, db_session, extraction_data, service):
        """Concepts missing required fields are filtered by validation; valid ones survive."""
        incomplete_concept = {
            "name": "Incomplete concept",
            # missing description, concept_type, difficulty
            "estimated_minutes": 10,
            "keywords": [],
            "examples": [],
        }
        api_response = _claude_api_response([CONCEPT_BINARY_SEARCH, incomplete_concept])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 1
        concepts = (
            db_session.query(Concept)
            .filter(Concept.subject_id == extraction_data["subject"].id)
            .all()
        )
        assert concepts[0].name == "Implement binary search on sorted array"

    @pytest.mark.asyncio
    async def test_invalid_concept_type_filtered_out(self, db_session, extraction_data, service):
        """Concepts with invalid concept_type are filtered by Pydantic validation."""
        bad_type_concept = {
            "name": "Bad type concept",
            "description": "This has an invalid type.",
            "concept_type": "unicorn_type",
            "difficulty": "beginner",
            "estimated_minutes": 10,
            "keywords": [],
            "examples": [],
        }
        api_response = _claude_api_response([CONCEPT_LINKED_LIST, bad_type_concept])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 1

    @pytest.mark.asyncio
    async def test_invalid_difficulty_filtered_out(self, db_session, extraction_data, service):
        """Concepts with invalid difficulty value are filtered."""
        bad_diff_concept = {
            "name": "Bad difficulty concept",
            "description": "This has an invalid difficulty.",
            "concept_type": "definition",
            "difficulty": "mythical",
            "estimated_minutes": 10,
            "keywords": [],
            "examples": [],
        }
        api_response = _claude_api_response([CONCEPT_STACK, bad_diff_concept])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 1

    @pytest.mark.asyncio
    async def test_empty_name_filtered_out(self, db_session, extraction_data, service):
        """Concepts with empty name fail Pydantic min_length=1 validation."""
        empty_name_concept = {
            "name": "",
            "description": "Has empty name.",
            "concept_type": "definition",
            "difficulty": "beginner",
            "estimated_minutes": 10,
            "keywords": [],
            "examples": [],
        }
        api_response = _claude_api_response([CONCEPT_BINARY_SEARCH, empty_name_concept])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 1

    @pytest.mark.asyncio
    async def test_all_concepts_invalid_returns_zero(self, db_session, extraction_data, service):
        """If ALL returned concepts are invalid, result is 0 with user-facing message."""
        bad_concepts = [
            {
                "name": "",
                "description": "Bad",
                "concept_type": "definition",
                "difficulty": "beginner",
                "estimated_minutes": 10,
                "keywords": [],
                "examples": [],
            },
            {
                "name": "Missing fields",
                "concept_type": "wrong",
                "difficulty": "beginner",
                "estimated_minutes": 10,
                "keywords": [],
                "examples": [],
            },
        ]
        api_response = _claude_api_response(bad_concepts)
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 0
        assert result.concept_ids == []
        assert result.message is not None
        assert "No concepts found" in result.message
        assert result.chunks_succeeded >= 1

    @pytest.mark.asyncio
    async def test_wrong_type_estimated_minutes_filtered(
        self, db_session, extraction_data, service
    ):
        """estimated_minutes as string should fail Pydantic validation."""
        wrong_type_concept = {
            "name": "Wrong type minutes",
            "description": "Has string instead of int for estimated_minutes.",
            "concept_type": "definition",
            "difficulty": "beginner",
            "estimated_minutes": "not a number",
            "keywords": [],
            "examples": [],
        }
        api_response = _claude_api_response([CONCEPT_STACK, wrong_type_concept])
        transport = _mock_transport(api_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts == 1


# ============================================================================
# Error handling — API failures
# ============================================================================


class TestAPIErrorHandling:
    """Test behavior when the Claude API returns errors."""

    @pytest.mark.asyncio
    async def test_api_500_on_all_chunks_raises_extraction_error(
        self, db_session, extraction_data, service
    ):
        """If every chunk gets a 500, ExtractionError is raised."""
        transport = _mock_transport({"error": "Internal server error"}, status_code=500)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ), pytest.raises(ExtractionError, match="All .* chunks failed"):
                await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

    @pytest.mark.asyncio
    async def test_no_api_key_raises_extraction_error(self, db_session, extraction_data, service):
        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = None
            with pytest.raises(ExtractionError, match="API key not configured"):
                await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    "Some content here.",
                    extraction_data["user"].id,
                    db_session,
                )

    @pytest.mark.asyncio
    async def test_malformed_json_in_response_text_fails_gracefully(
        self, db_session, extraction_data, service
    ):
        """If Claude returns invalid JSON in content[0].text, all chunks fail."""
        bad_response = {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "this is not json {{{"}],
            "model": "claude-haiku-4-5",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 10},
        }
        transport = _mock_transport(bad_response)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ), pytest.raises(ExtractionError, match="All .* chunks failed"):
                await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

    @pytest.mark.asyncio
    async def test_rate_limit_429_with_retry_succeeds(self, db_session, extraction_data, service):
        """429 rate limit followed by success should work (service has retry logic)."""
        success_response = _claude_api_response([CONCEPT_BINARY_SEARCH])
        call_count = 0

        async def rate_limit_then_succeed(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:
                return httpx.Response(
                    status_code=429,
                    headers={"retry-after": "0"},
                    json={"error": "rate limited"},
                    request=request,
                )
            return httpx.Response(
                status_code=200,
                json=success_response,
                request=request,
            )

        transport = httpx.MockTransport(rate_limit_then_succeed)

        with patch("app.services.concept_extraction.claude_service") as mock_cs:
            mock_cs.api_key = "test-key"
            mock_cs.base_url = "https://api.anthropic.com/v1"
            mock_cs._get_headers.return_value = {
                "x-api-key": "test-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            with patch(
                "app.services.concept_extraction.httpx.AsyncClient",
                _patched_async_client(transport),
            ):
                result = await service.extract_concepts(
                    extraction_data["content"].id,
                    extraction_data["subject"].id,
                    extraction_data["content"].extracted_text,
                    extraction_data["user"].id,
                    db_session,
                )

        assert result.created_concepts >= 1
        assert result.chunks_succeeded >= 1
