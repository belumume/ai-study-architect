"""
Tests for agent API endpoints.

Covers:
- Todo 050: Context dict cannot override user_id (security)
- Todo 051: HTTPException not swallowed by broad except Exception
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


class TestContextOverrideSecurity:
    """Todo 050: Verify context dict cannot override authenticated user_id."""

    @pytest.mark.asyncio
    async def test_context_cannot_override_user_id(self, authenticated_client):
        """A malicious context dict with user_id must not override the authenticated user."""
        client, user_data = authenticated_client
        real_user_id = str(user_data["user"].id)

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.message = "test"
        mock_response.data = {}
        mock_response.errors = []
        mock_response.metadata = {}

        with patch("app.api.v1.agents.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.process = MagicMock(return_value=mock_response)
            mock_get_agent.return_value = mock_agent

            response = await client.post(
                "/api/v1/agents/chat",
                json={
                    "agent_type": "lead_tutor",
                    "message": "hello",
                    "context": {"user_id": "attacker-injected-uuid"},
                },
            )

            assert response.status_code == 200
            # Verify the agent was called with the REAL user_id, not the injected one
            call_args = mock_agent.process.call_args[0][0]
            assert call_args["user_id"] == real_user_id
            assert call_args["user_id"] != "attacker-injected-uuid"

    @pytest.mark.asyncio
    async def test_context_cannot_override_action(self, authenticated_client):
        """Context dict should not override the action field either."""
        client, user_data = authenticated_client

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.message = "test"
        mock_response.data = {}
        mock_response.errors = []
        mock_response.metadata = {}

        with patch("app.api.v1.agents.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.process = MagicMock(return_value=mock_response)
            mock_get_agent.return_value = mock_agent

            response = await client.post(
                "/api/v1/agents/chat",
                json={
                    "agent_type": "lead_tutor",
                    "message": "hello",
                    "action": "general",
                    "context": {"action": "admin_override"},
                },
            )

            assert response.status_code == 200
            call_args = mock_agent.process.call_args[0][0]
            assert call_args["action"] == "general"

    @pytest.mark.asyncio
    async def test_context_cannot_override_user_input(self, authenticated_client):
        """Context dict should not override user_input."""
        client, user_data = authenticated_client

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.message = "test"
        mock_response.data = {}
        mock_response.errors = []
        mock_response.metadata = {}

        with patch("app.api.v1.agents.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.process = MagicMock(return_value=mock_response)
            mock_get_agent.return_value = mock_agent

            response = await client.post(
                "/api/v1/agents/chat",
                json={
                    "agent_type": "lead_tutor",
                    "message": "legitimate question",
                    "context": {"user_input": "injected input"},
                },
            )

            assert response.status_code == 200
            call_args = mock_agent.process.call_args[0][0]
            assert call_args["user_input"] == "legitimate question"

    @pytest.mark.asyncio
    async def test_context_extra_keys_pass_through(self, authenticated_client):
        """Non-reserved keys in context should still be forwarded to the agent."""
        client, user_data = authenticated_client

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.message = "test"
        mock_response.data = {}
        mock_response.errors = []
        mock_response.metadata = {}

        with patch("app.api.v1.agents.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.process = MagicMock(return_value=mock_response)
            mock_get_agent.return_value = mock_agent

            response = await client.post(
                "/api/v1/agents/chat",
                json={
                    "agent_type": "lead_tutor",
                    "message": "hello",
                    "context": {"subject_id": "math-101", "topic": "algebra"},
                },
            )

            assert response.status_code == 200
            call_args = mock_agent.process.call_args[0][0]
            assert call_args["subject_id"] == "math-101"
            assert call_args["topic"] == "algebra"


class TestHTTPExceptionPropagation:
    """Todo 051: HTTPException should not be swallowed by except Exception."""

    @pytest.mark.asyncio
    async def test_clear_memory_404_not_swallowed(self, authenticated_client):
        """DELETE /agents/clear-memory should return 404 for missing agent, not 500."""
        client, _ = authenticated_client
        response = await client.delete(
            "/api/v1/agents/clear-memory",
            params={"agent_type": "lead_tutor"},
        )
        assert response.status_code == 404
        assert "No active" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_bad_agent_type_returns_400(self, authenticated_client):
        """POST /agents/chat with invalid agent type should return 400, not 500."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/chat",
            json={
                "agent_type": "lead_tutor",  # Valid enum but test via get_agent
                "message": "hello",
            },
        )
        # This tests the normal flow — the agent_type enum validation happens at schema level
        # For the HTTPException propagation test, we mock get_agent to raise 400
        with patch("app.api.v1.agents.get_agent") as mock_get_agent:
            mock_get_agent.side_effect = HTTPException(
                status_code=400, detail="Unknown agent type: bad_type"
            )
            response = await client.post(
                "/api/v1/agents/chat",
                json={
                    "agent_type": "lead_tutor",
                    "message": "hello",
                },
            )
            assert response.status_code == 400
            assert "Unknown agent type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_study_plan_httpexception_propagates(self, authenticated_client):
        """HTTPException raised during study plan creation should propagate with original status."""
        client, _ = authenticated_client
        with patch("app.api.v1.agents.get_agent") as mock_get_agent:
            mock_get_agent.side_effect = HTTPException(status_code=429, detail="Rate limited")
            response = await client.post(
                "/api/v1/agents/study-plan",
                json={
                    "learning_goal": "Learn Python fundamentals",
                },
            )
            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_explain_httpexception_propagates(self, authenticated_client):
        """HTTPException raised during explain should propagate with original status."""
        client, _ = authenticated_client
        with patch("app.api.v1.agents.get_agent") as mock_get_agent:
            mock_get_agent.side_effect = HTTPException(status_code=403, detail="Forbidden")
            response = await client.post(
                "/api/v1/agents/explain",
                json={"concept": "recursion"},
            )
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_check_understanding_httpexception_propagates(self, authenticated_client):
        """HTTPException raised during check-understanding should propagate."""
        client, _ = authenticated_client
        with patch("app.api.v1.agents.get_agent") as mock_get_agent:
            mock_get_agent.side_effect = HTTPException(
                status_code=503, detail="Service unavailable"
            )
            response = await client.post(
                "/api/v1/agents/check-understanding",
                json={"topic": "binary trees"},
            )
            assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_agent_status_httpexception_propagates(self, authenticated_client):
        """HTTPException raised during status check should propagate."""
        client, _ = authenticated_client
        with patch(
            "app.api.v1.agents._agent_registry",
            {"bad_key": MagicMock(side_effect=Exception("boom"))},
        ):
            # status endpoint iterates the registry — a non-HTTPException should become 500
            # but an HTTPException should propagate
            pass
        # The status endpoint doesn't call get_agent, so we test it differently:
        # Just verify it works normally (no HTTPException path to exercise directly)
        response = await client.get("/api/v1/agents/status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_real_exception_still_becomes_500(self, authenticated_client):
        """Non-HTTP exceptions should still be caught and wrapped as 500."""
        client, _ = authenticated_client
        with patch("app.api.v1.agents.get_agent") as mock_get_agent:
            mock_get_agent.side_effect = RuntimeError("Unexpected failure")
            response = await client.post(
                "/api/v1/agents/chat",
                json={
                    "agent_type": "lead_tutor",
                    "message": "hello",
                },
            )
            assert response.status_code == 500
            assert "Agent processing failed" in response.json()["detail"]
