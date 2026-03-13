"""Tests for OpenAI fallback service."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

from app.services.openai_fallback import OpenAIFallbackService


class TestOpenAIFallbackService:
    @pytest.fixture
    def service(self):
        return OpenAIFallbackService()

    def test_default_model(self, service):
        assert service.model == "gpt-3.5-turbo"

    @patch.dict("os.environ", {"OPENAI_MODEL": "gpt-4"})
    def test_custom_model(self):
        svc = OpenAIFallbackService()
        assert svc.model == "gpt-4"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123"})
    def test_api_key_from_env(self, service):
        assert service.api_key == "sk-test123"

    @patch.dict("os.environ", {}, clear=True)
    def test_api_key_missing(self):
        svc = OpenAIFallbackService()
        assert svc.api_key is None

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123"})
    def test_enabled_with_key(self, service):
        assert service.enabled is True

    @patch.dict("os.environ", {}, clear=True)
    def test_disabled_without_key(self):
        svc = OpenAIFallbackService()
        assert svc.enabled is False

    @pytest.mark.asyncio
    @patch.dict("os.environ", {}, clear=True)
    async def test_chat_completion_disabled(self):
        svc = OpenAIFallbackService()
        result = await svc.chat_completion([{"role": "user", "content": "hello"}])
        assert "error" in result
        assert "not configured" in result["error"]

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123"})
    async def test_chat_completion_success(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello! How can I help?"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.chat_completion([{"role": "user", "content": "hello"}])

        assert result["response"] == "Hello! How can I help?"
        assert result["done"] is True
        assert "usage" in result

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123"})
    async def test_chat_completion_with_max_tokens(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Short."}}],
            "usage": {},
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.chat_completion(
                [{"role": "user", "content": "hi"}],
                max_tokens=10,
            )

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert payload["max_tokens"] == 10

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123"})
    async def test_chat_completion_api_error(self, service):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.chat_completion([{"role": "user", "content": "hello"}])

        assert "error" in result
        assert "Failed to get AI response" in result["response"]

    @pytest.mark.asyncio
    @patch.dict("os.environ", {}, clear=True)
    async def test_health_check_disabled(self):
        svc = OpenAIFallbackService()
        assert await svc.health_check() is False

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123"})
    async def test_health_check_success(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            assert await service.health_check() is True

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123"})
    async def test_health_check_failure(self, service):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            assert await service.health_check() is False
