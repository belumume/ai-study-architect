"""
Tests for dashboard summary endpoint.

Covers: empty state (0 concepts), subject listing, mastery aggregation.
"""


import pytest

from app.models.subject import Subject


class TestDashboardEndpoint:
    @pytest.mark.asyncio
    async def test_dashboard_requires_auth(self, client):
        response = await client.get("/api/v1/dashboard/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_dashboard_empty_state(self, authenticated_client):
        """Dashboard works with no subjects, sessions, or concepts."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/dashboard/")
        assert response.status_code == 200
        data = response.json()

        assert data["today_minutes"] == 0
        assert data["week_minutes"] == 0
        assert data["current_streak"] == 0
        assert data["active_session_id"] is None
        assert data["subjects"] == []
        assert len(data["heatmap"]) == 28
        assert data["total_concepts"] == 0
        assert data["mastered_concepts"] == 0
        assert data["mastery_index"] is None

    @pytest.mark.asyncio
    async def test_dashboard_with_subjects_zero_concepts(self, authenticated_client, db_session):
        """Dashboard works with subjects but 0 concepts (pre-extraction state)."""
        client, user_data = authenticated_client
        user = user_data["user"]

        subject = Subject(user_id=user.id, name="Algorithms", color="#D4FF00")
        db_session.add(subject)
        db_session.commit()

        response = await client.get("/api/v1/dashboard/")
        assert response.status_code == 200
        data = response.json()

        assert len(data["subjects"]) == 1
        assert data["subjects"][0]["name"] == "Algorithms"
        assert data["total_concepts"] == 0
        assert data["mastered_concepts"] == 0
        assert data["mastery_index"] is None

    @pytest.mark.asyncio
    async def test_dashboard_heatmap_has_28_days(self, authenticated_client):
        """Heatmap always returns exactly 28 days regardless of data."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/dashboard/")
        data = response.json()

        assert len(data["heatmap"]) == 28
        for day in data["heatmap"]:
            assert "date" in day
            assert "minutes" in day
            assert day["minutes"] >= 0
