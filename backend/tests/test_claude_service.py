"""Tests for Claude (Anthropic) service."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.claude_service import ClaudeService


class TestClaudeService:
    @pytest.fixture
    def service(self):
        return ClaudeService()

    def test_default_model(self, service):
        assert "claude" in service.model

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"})
    def test_api_key_from_env(self, service):
        assert service.api_key == "sk-ant-test"

    @patch.dict("os.environ", {}, clear=True)
    def test_api_key_missing(self):
        svc = ClaudeService()
        assert svc.api_key is None

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"})
    def test_enabled_with_key(self, service):
        assert service.enabled is True

    @patch.dict("os.environ", {}, clear=True)
    def test_disabled_without_key(self):
        svc = ClaudeService()
        assert svc.enabled is False

    def test_get_headers(self, service):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            headers = service._get_headers()
            assert headers["x-api-key"] == "sk-ant-test"
            assert "anthropic-version" in headers
            assert headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    @patch.dict("os.environ", {}, clear=True)
    async def test_chat_completion_disabled(self):
        svc = ClaudeService()
        result = await svc.chat_completion([{"role": "user", "content": "hello"}])
        assert "error" in result
        assert "not configured" in result["error"]

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"})
    async def test_chat_completion_success(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "A BST is a tree structure."}],
            "usage": {"input_tokens": 10, "output_tokens": 8},
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.chat_completion([{"role": "user", "content": "What is a BST?"}])

        assert result["response"] == "A BST is a tree structure."
        assert result["done"] is True
        assert "usage" in result

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"})
    async def test_chat_completion_with_system_message(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Response"}],
            "usage": {},
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await service.chat_completion(
                [
                    {"role": "system", "content": "You are a tutor."},
                    {"role": "user", "content": "hello"},
                ]
            )

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert payload.get("system") == "You are a tutor."
            assert payload["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"})
    async def test_chat_completion_api_error(self, service):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.chat_completion([{"role": "user", "content": "hello"}])

        assert "error" in result

    @pytest.mark.asyncio
    @patch.dict("os.environ", {}, clear=True)
    async def test_health_check_disabled(self):
        svc = ClaudeService()
        assert await svc.health_check() is False

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"})
    async def test_health_check_success(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 405

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            assert await service.health_check() is True

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"})
    async def test_health_check_failure(self, service):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            assert await service.health_check() is False
