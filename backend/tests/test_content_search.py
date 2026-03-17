"""
Tests for content search with prefix matching (todo 046).

Verifies that:
- Partial/prefix queries ("algo") match full words ("algorithm")
- Multi-word queries use AND + prefix on last word
- tsquery special characters are sanitized (no injection)
- Empty/whitespace-only queries after sanitization return empty results
- Full-word queries still work as before
"""

import uuid

import pytest

from app.api.v1.content import _build_prefix_tsquery, _sanitize_tsquery_word
from app.models.content import Content
from app.models.user import User


@pytest.fixture
def search_content_set(db_session, authenticated_client):
    """Create a set of content items with varied titles/descriptions for search testing."""
    _, user_data = authenticated_client
    user = user_data["user"]

    items = []
    test_data = [
        {
            "title": "Introduction to Algorithms",
            "description": "Covers sorting, searching, and graph algorithms",
            "extracted_text": "Binary search is a divide-and-conquer algorithm.",
        },
        {
            "title": "Data Structures in Python",
            "description": "Lists, trees, hash maps, and heaps",
            "extracted_text": "A binary tree is a hierarchical data structure.",
        },
        {
            "title": "Machine Learning Fundamentals",
            "description": "Neural networks, gradient descent, backpropagation",
            "extracted_text": "Supervised learning uses labeled training data.",
        },
        {
            "title": "Database Systems",
            "description": "SQL, indexing, normalization, transactions",
            "extracted_text": "PostgreSQL supports full-text search with tsvector.",
        },
    ]

    for i, data in enumerate(test_data):
        file_id = uuid.uuid4()
        content = Content(
            id=file_id,
            user_id=user.id,
            title=data["title"],
            description=data["description"],
            content_type="document",
            processing_status="completed",
            extracted_text=data["extracted_text"],
            file_path=f"uploads/test/{file_id}.pdf",
            file_size=1024 * (i + 1),
            mime_type="application/pdf",
            file_hash=f"{i:064x}",
            original_filename=f"test_doc_{i}.pdf",
        )
        db_session.add(content)
        items.append(content)

    db_session.commit()
    for item in items:
        db_session.refresh(item)

    return items


class TestBuildPrefixTsquery:
    """Unit tests for the tsquery builder helper."""

    def test_single_word_gets_prefix(self):
        assert _build_prefix_tsquery("algo") == "algo:*"

    def test_multi_word_last_gets_prefix(self):
        assert _build_prefix_tsquery("data struct") == "data & struct:*"

    def test_three_words(self):
        assert _build_prefix_tsquery("binary search tree") == "binary & search & tree:*"

    def test_strips_special_characters(self):
        assert _build_prefix_tsquery("algo&rithm") == "algorithm:*"
        assert _build_prefix_tsquery("test|injection") == "testinjection:*"
        assert _build_prefix_tsquery("hack!") == "hack:*"
        assert _build_prefix_tsquery("(parens)") == "parens:*"
        assert _build_prefix_tsquery("colon:star*") == "colonstar:*"

    def test_all_special_chars_returns_empty(self):
        assert _build_prefix_tsquery("&|!()") == ""
        assert _build_prefix_tsquery("***") == ""

    def test_whitespace_only_returns_empty(self):
        assert _build_prefix_tsquery("   ") == ""

    def test_mixed_valid_and_empty_words(self):
        # "& algo" -> first word sanitizes to empty, second to "algo"
        assert _build_prefix_tsquery("& algo") == "algo:*"

    def test_preserves_numbers(self):
        assert _build_prefix_tsquery("python3") == "python3:*"

    def test_hyphenated_word_splits(self):
        # Hyphens replaced with spaces — "well-known" becomes two words
        assert _build_prefix_tsquery("well-known") == "well & known:*"

    def test_single_full_word(self):
        assert _build_prefix_tsquery("algorithm") == "algorithm:*"


class TestSanitizeTsqueryWord:
    """Unit tests for the word sanitizer."""

    def test_clean_word_unchanged(self):
        assert _sanitize_tsquery_word("hello") == "hello"

    def test_strips_ampersand(self):
        assert _sanitize_tsquery_word("a&b") == "ab"

    def test_strips_pipe(self):
        assert _sanitize_tsquery_word("a|b") == "ab"

    def test_strips_exclamation(self):
        assert _sanitize_tsquery_word("not!") == "not"

    def test_strips_parens(self):
        assert _sanitize_tsquery_word("(group)") == "group"

    def test_strips_colon_and_star(self):
        assert _sanitize_tsquery_word("prefix:*") == "prefix"

    def test_strips_backslash(self):
        assert _sanitize_tsquery_word("back\\slash") == "backslash"

    def test_strips_angle_brackets(self):
        assert _sanitize_tsquery_word("<followed_by>") == "followed_by"

    def test_strips_single_quote(self):
        assert _sanitize_tsquery_word("it's") == "its"

    def test_preserves_hyphen_in_word(self):
        # _sanitize_tsquery_word doesn't touch hyphens (they're not tsquery operators)
        # but _build_prefix_tsquery replaces hyphens with spaces before splitting
        assert _sanitize_tsquery_word("well-known") == "well-known"

    def test_all_special_returns_empty(self):
        assert _sanitize_tsquery_word("&|!") == ""


class TestSearchEndpointPrefixMatching:
    """Integration tests for prefix search via the API endpoint."""

    @pytest.mark.asyncio
    async def test_prefix_single_word_matches(self, authenticated_client, search_content_set):
        """'algo' should match 'Introduction to Algorithms'."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/content/search", params={"q": "algo"})
        assert response.status_code == 200
        results = response.json()
        titles = [r["title"] for r in results]
        assert any("Algorithm" in t for t in titles)

    @pytest.mark.asyncio
    async def test_prefix_matches_description(self, authenticated_client, search_content_set):
        """'neural' prefix should match ML content via description."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/content/search", params={"q": "neur"})
        assert response.status_code == 200
        results = response.json()
        titles = [r["title"] for r in results]
        assert any("Machine Learning" in t for t in titles)

    @pytest.mark.asyncio
    async def test_prefix_matches_extracted_text(self, authenticated_client, search_content_set):
        """'tsvector' prefix should match Database Systems via extracted text."""
        client, _ = authenticated_client
        # "tsvect" is a prefix of "tsvector"
        response = await client.get("/api/v1/content/search", params={"q": "tsvect"})
        assert response.status_code == 200
        results = response.json()
        titles = [r["title"] for r in results]
        assert any("Database" in t for t in titles)

    @pytest.mark.asyncio
    async def test_full_word_still_works(self, authenticated_client, search_content_set):
        """Full word 'algorithm' should still match."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/content/search", params={"q": "algorithm"})
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0
        titles = [r["title"] for r in results]
        assert any("Algorithm" in t for t in titles)

    @pytest.mark.asyncio
    async def test_multi_word_prefix(self, authenticated_client, search_content_set):
        """'data struct' should match 'Data Structures in Python'."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/content/search", params={"q": "data struct"})
        assert response.status_code == 200
        results = response.json()
        titles = [r["title"] for r in results]
        assert any("Data Structures" in t for t in titles)

    @pytest.mark.asyncio
    async def test_multi_word_all_must_match(self, authenticated_client, search_content_set):
        """'machine database' should return nothing (no content has both)."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/content/search", params={"q": "machine database"})
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_query_too_short_returns_422(self, authenticated_client, search_content_set):
        """Single character query should be rejected."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/content/search", params={"q": "a"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_special_chars_sanitized(self, authenticated_client, search_content_set):
        """Queries with tsquery special chars should not cause errors."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/content/search", params={"q": "algo&rithm"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_only_special_chars_returns_empty(self, authenticated_client, search_content_set):
        """Query that is all special chars (after length check) returns empty."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/content/search", params={"q": "&|!()"})
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_no_cross_user_results(
        self, authenticated_client, search_content_set, db_session
    ):
        """Search should only return the current user's content."""
        client, _ = authenticated_client
        from app.core.security import get_password_hash

        other_user = User(
            email=f"other_{uuid.uuid4().hex[:8]}@example.com",
            username=f"other_{uuid.uuid4().hex[:8]}",
            hashed_password=get_password_hash("testpassword"),
            full_name="Other User",
            is_active=True,
            is_verified=True,
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_content = Content(
            id=uuid.uuid4(),
            user_id=other_user.id,
            title="Algorithms for Other User",
            content_type="document",
            processing_status="completed",
            extracted_text="This should not appear in search results.",
            file_path="uploads/other/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            file_hash="f" * 64,
            original_filename="other.pdf",
        )
        db_session.add(other_content)
        db_session.commit()

        response = await client.get("/api/v1/content/search", params={"q": "algo"})
        assert response.status_code == 200
        results = response.json()
        for r in results:
            assert r["title"] != "Algorithms for Other User"
