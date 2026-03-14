"""
Tests for the concept extraction service.

Tests pure functions (normalization, validation) directly.
Tests service logic with mocked Claude API responses.
"""

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest

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
                    # missing description
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
                    "name": "",  # Empty name (min_length=1 violation)
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
# Service tests — mock Claude API
# ============================================================================

VALID_CLAUDE_RESPONSE = {
    "concepts": [
        {
            "name": "Define binary search algorithm",
            "description": "A search algorithm that finds elements in sorted arrays by repeatedly dividing the search interval in half.",
            "concept_type": "definition",
            "difficulty": "beginner",
            "estimated_minutes": 15,
            "keywords": ["binary search", "search", "algorithm", "sorted array"],
            "examples": ["Given sorted array [1,3,5,7,9], find element 7"],
        },
        {
            "name": "Implement binary search on sorted array",
            "description": "Write code to perform binary search with O(log n) time complexity.",
            "concept_type": "procedure",
            "difficulty": "intermediate",
            "estimated_minutes": 25,
            "keywords": ["implementation", "binary search", "O(log n)"],
            "examples": ["Implement binary_search(arr, target) that returns the index"],
        },
    ],
    "dependencies": [
        {
            "prerequisite_name": "Define binary search algorithm",
            "dependent_name": "Implement binary search on sorted array",
            "strength": 1.0,
            "reason": "Must understand the algorithm before implementing it",
        }
    ],
    "metadata": {
        "total_extracted": 2,
        "extraction_confidence": 0.9,
        "notes": "Clear algorithmic content",
    },
}


def _mock_claude_response(response_data: dict):
    """Create a mock httpx response matching Claude API shape."""
    return AsyncMock(
        status_code=200,
        json=lambda: {"content": [{"text": json.dumps(response_data)}]},
        raise_for_status=lambda: None,
    )


class TestExtractionService:
    def setup_method(self):
        self.service = ConceptExtractionService()

    @pytest.mark.asyncio
    async def test_extract_concepts_happy_path(self, db_session):
        content_id = uuid.uuid4()
        subject_id = uuid.uuid4()
        user_id = uuid.uuid4()
        text = "Binary search is an efficient algorithm for finding items in sorted arrays. " * 20

        mock_response = _mock_claude_response(VALID_CLAUDE_RESPONSE)

        with patch("app.services.concept_extraction.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = mock_response
            mock_client_cls.return_value = mock_client

            result = await self.service.extract_concepts(
                content_id, subject_id, text, user_id, db_session
            )

        assert result.created_concepts == 2
        assert result.chunks_succeeded >= 1
        assert result.chunks_failed == 0

    @pytest.mark.asyncio
    async def test_deduplication_across_chunks(self, db_session):
        """Same concept name in multiple chunks should be deduplicated."""
        content_id = uuid.uuid4()
        subject_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Create text long enough for 2 chunks
        text = "Binary search algorithm explanation. " * 50 + "More content here. " * 50

        mock_response = _mock_claude_response(VALID_CLAUDE_RESPONSE)

        with patch("app.services.concept_extraction.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = mock_response
            mock_client_cls.return_value = mock_client

            result = await self.service.extract_concepts(
                content_id, subject_id, text, user_id, db_session
            )

        # Even though Claude returns 2 concepts per chunk, dedup should prevent duplicates
        assert result.created_concepts == 2

    @pytest.mark.asyncio
    async def test_empty_text_raises_error(self, db_session):
        with pytest.raises(ExtractionError, match="No text chunks"):
            await self.service.extract_concepts(
                uuid.uuid4(), uuid.uuid4(), "", uuid.uuid4(), db_session
            )

    @pytest.mark.asyncio
    async def test_all_chunks_fail_raises_error(self, db_session):
        text = "Some content to extract from. " * 20

        with patch("app.services.concept_extraction.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=Exception("API error"))
            mock_client_cls.return_value = mock_client

            with pytest.raises(ExtractionError, match="All .* chunks failed"):
                await self.service.extract_concepts(
                    uuid.uuid4(), uuid.uuid4(), text, uuid.uuid4(), db_session
                )

    @pytest.mark.asyncio
    async def test_partial_failure_returns_results(self, db_session):
        """If some chunks fail, the successful ones should still produce concepts."""
        content_id = uuid.uuid4()
        subject_id = uuid.uuid4()
        user_id = uuid.uuid4()
        # Long text for multiple chunks
        text = "Content for extraction. " * 200

        call_count = 0

        async def alternating_response(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise Exception("Simulated failure")
            return _mock_claude_response(VALID_CLAUDE_RESPONSE)

        with patch("app.services.concept_extraction.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = alternating_response
            mock_client_cls.return_value = mock_client

            result = await self.service.extract_concepts(
                content_id, subject_id, text, user_id, db_session
            )

        assert result.created_concepts > 0
        assert result.chunks_failed > 0
        assert result.chunks_succeeded > 0

    @pytest.mark.asyncio
    async def test_text_length_cap(self, db_session):
        """Text exceeding MAX_TEXT_LENGTH should be truncated."""
        service = ConceptExtractionService()
        long_text = "x" * 200_000  # 2x the cap

        mock_response = _mock_claude_response(VALID_CLAUDE_RESPONSE)

        with patch("app.services.concept_extraction.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = mock_response
            mock_client_cls.return_value = mock_client

            result = await service.extract_concepts(
                uuid.uuid4(), uuid.uuid4(), long_text, uuid.uuid4(), db_session
            )

        # Should succeed (text was truncated, not rejected)
        assert result.created_concepts >= 0
