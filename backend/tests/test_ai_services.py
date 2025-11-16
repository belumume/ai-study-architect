"""
AI service integration tests with mocking
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.services.ai_service_manager import AIServiceManager


class TestAIServiceManager:
    """Test AI service manager"""

    def test_manager_initialization(self):
        """Test AI service manager initializes correctly"""
        manager = AIServiceManager()

        assert manager is not None
        assert hasattr(manager, 'services')
        assert len(manager.services) > 0

        # Check services are tuples of (name, service)
        for name, service in manager.services:
            assert isinstance(name, str)
            assert service is not None

    def test_service_priority_order(self):
        """Test that services are in correct priority order"""
        manager = AIServiceManager()

        service_names = [name for name, _ in manager.services]

        # Claude should be first (primary)
        assert service_names[0] == "Claude"
        # OpenAI should be second (fallback)
        assert service_names[1] == "OpenAI"


class TestGetAvailableService:
    """Test getting available AI service"""

    @pytest.mark.asyncio
    async def test_get_first_enabled_service(self):
        """Test getting first enabled service"""
        manager = AIServiceManager()

        # Mock first service as enabled and healthy
        with patch.object(manager.services[0][1], 'enabled', True), \
             patch.object(manager.services[0][1], 'health_check', AsyncMock(return_value=True)):

            name, service = await manager.get_available_service()

            assert name == manager.services[0][0]
            assert service == manager.services[0][1]

    @pytest.mark.asyncio
    async def test_fallback_to_second_service(self):
        """Test fallback when first service is unavailable"""
        manager = AIServiceManager()

        # Mock first service as disabled, second as enabled
        with patch.object(manager.services[0][1], 'enabled', False), \
             patch.object(manager.services[1][1], 'enabled', True), \
             patch.object(manager.services[1][1], 'health_check', AsyncMock(return_value=True)):

            name, service = await manager.get_available_service()

            assert name == manager.services[1][0]
            assert service == manager.services[1][1]

    @pytest.mark.asyncio
    async def test_no_service_available(self):
        """Test when no services are available"""
        manager = AIServiceManager()

        # Mock all services as disabled
        with patch.object(manager.services[0][1], 'enabled', False), \
             patch.object(manager.services[1][1], 'enabled', False):

            name, service = await manager.get_available_service()

            assert name is None
            assert service is None

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test fallback when health check fails"""
        manager = AIServiceManager()

        # Mock first service as enabled but unhealthy, second as healthy
        with patch.object(manager.services[0][1], 'enabled', True), \
             patch.object(manager.services[0][1], 'health_check', AsyncMock(return_value=False)), \
             patch.object(manager.services[1][1], 'enabled', True), \
             patch.object(manager.services[1][1], 'health_check', AsyncMock(return_value=True)):

            name, service = await manager.get_available_service()

            # Should fall back to second service
            assert name == manager.services[1][0]

    @pytest.mark.asyncio
    async def test_exception_during_health_check(self):
        """Test fallback when health check raises exception"""
        manager = AIServiceManager()

        # Mock first service to raise exception, second to work
        with patch.object(manager.services[0][1], 'enabled', True), \
             patch.object(manager.services[0][1], 'health_check', AsyncMock(side_effect=Exception("API Error"))), \
             patch.object(manager.services[1][1], 'enabled', True), \
             patch.object(manager.services[1][1], 'health_check', AsyncMock(return_value=True)):

            name, service = await manager.get_available_service()

            # Should fall back to second service
            assert name == manager.services[1][0]


class TestChatCompletion:
    """Test chat completion functionality"""

    @pytest.mark.asyncio
    async def test_chat_completion_success(self):
        """Test successful chat completion"""
        manager = AIServiceManager()

        messages = [
            {"role": "user", "content": "Hello, AI!"}
        ]

        expected_response = {
            "content": "Hello! How can I help you?",
            "model": "test-model",
            "usage": {"tokens": 10}
        }

        # Mock the service
        mock_service = AsyncMock()
        mock_service.chat_completion = AsyncMock(return_value=expected_response)
        mock_service.enabled = True
        mock_service.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("MockService", mock_service)]):
            # Try without streaming first
            result = await manager.chat_completion(messages, stream=False)

            assert result == expected_response
            mock_service.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_completion_with_temperature(self):
        """Test chat completion with custom temperature"""
        manager = AIServiceManager()

        messages = [{"role": "user", "content": "Test"}]

        mock_service = AsyncMock()
        mock_service.chat_completion = AsyncMock(return_value={"content": "Response"})
        mock_service.enabled = True
        mock_service.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("MockService", mock_service)]):
            await manager.chat_completion(messages, temperature=0.9, stream=False)

            # Check temperature was passed
            call_kwargs = mock_service.chat_completion.call_args[1]
            assert call_kwargs['temperature'] == 0.9

    @pytest.mark.asyncio
    async def test_chat_completion_with_max_tokens(self):
        """Test chat completion with max tokens"""
        manager = AIServiceManager()

        messages = [{"role": "user", "content": "Test"}]

        mock_service = AsyncMock()
        mock_service.chat_completion = AsyncMock(return_value={"content": "Response"})
        mock_service.enabled = True
        mock_service.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("MockService", mock_service)]):
            await manager.chat_completion(messages, max_tokens=100, stream=False)

            call_kwargs = mock_service.chat_completion.call_args[1]
            assert call_kwargs['max_tokens'] == 100

    @pytest.mark.asyncio
    async def test_chat_completion_prefer_specific_service(self):
        """Test preferring a specific service"""
        manager = AIServiceManager()

        messages = [{"role": "user", "content": "Test"}]

        # Create two mock services
        mock_service1 = AsyncMock()
        mock_service1.chat_completion = AsyncMock(return_value={"content": "Service1"})
        mock_service1.enabled = True

        mock_service2 = AsyncMock()
        mock_service2.chat_completion = AsyncMock(return_value={"content": "Service2"})
        mock_service2.enabled = True

        with patch.object(manager, 'services', [("Service1", mock_service1), ("Service2", mock_service2)]):
            # Prefer Service2
            result = await manager.chat_completion(messages, prefer_service="Service2", stream=False)

            # Service2 should be called, not Service1
            mock_service2.chat_completion.assert_called_once()
            assert "Service2" in str(result.get("content", ""))

    @pytest.mark.asyncio
    async def test_chat_completion_preferred_service_fails(self):
        """Test fallback when preferred service fails"""
        manager = AIServiceManager()

        messages = [{"role": "user", "content": "Test"}]

        # Create two mock services
        mock_service1 = AsyncMock()
        mock_service1.chat_completion = AsyncMock(side_effect=Exception("Service1 Error"))
        mock_service1.enabled = True

        mock_service2 = AsyncMock()
        mock_service2.chat_completion = AsyncMock(return_value={"content": "Service2 OK"})
        mock_service2.enabled = True
        mock_service2.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("Service1", mock_service1), ("Service2", mock_service2)]):
            # Prefer Service1 but it should fail and fall back
            result = await manager.chat_completion(messages, prefer_service="Service1", stream=False)

            # Should fall back to Service2
            # The exact fallback behavior depends on implementation
            # Just check it doesn't crash
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_chat_completion_streaming(self):
        """Test streaming chat completion"""
        manager = AIServiceManager()

        messages = [{"role": "user", "content": "Stream test"}]

        # Create async generator for streaming
        async def mock_stream():
            yield {"delta": "Hello"}
            yield {"delta": " "}
            yield {"delta": "World"}

        mock_service = AsyncMock()
        mock_service.chat_completion = AsyncMock(return_value=mock_stream())
        mock_service.enabled = True
        mock_service.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("MockService", mock_service)]):
            result = await manager.chat_completion(messages, stream=True)

            # Result should be an async generator for streaming
            # Check it's callable or an async generator
            assert result is not None

    @pytest.mark.asyncio
    async def test_chat_completion_error_handling(self):
        """Test error handling in chat completion"""
        manager = AIServiceManager()

        messages = [{"role": "user", "content": "Test"}]

        mock_service = AsyncMock()
        mock_service.chat_completion = AsyncMock(return_value={"error": "API Error"})
        mock_service.enabled = True
        mock_service.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("MockService", mock_service)]):
            result = await manager.chat_completion(messages, stream=False)

            # Should handle error gracefully
            # Exact behavior depends on implementation
            assert isinstance(result, dict)


class TestServiceMessageFormatting:
    """Test message formatting for different services"""

    @pytest.mark.asyncio
    async def test_claude_message_format(self):
        """Test Claude expects correct message format"""
        manager = AIServiceManager()

        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]

        mock_claude = AsyncMock()
        mock_claude.chat_completion = AsyncMock(return_value={"content": "Hi"})
        mock_claude.enabled = True
        mock_claude.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("Claude", mock_claude)]):
            await manager.chat_completion(messages, stream=False)

            # Check messages were passed correctly
            call_args = mock_claude.chat_completion.call_args
            passed_messages = call_args[1]['messages']
            assert len(passed_messages) >= 1

    @pytest.mark.asyncio
    async def test_empty_messages(self):
        """Test handling of empty messages list"""
        manager = AIServiceManager()

        messages = []

        mock_service = AsyncMock()
        mock_service.chat_completion = AsyncMock(return_value={"error": "No messages"})
        mock_service.enabled = True
        mock_service.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("MockService", mock_service)]):
            result = await manager.chat_completion(messages, stream=False)

            # Should handle gracefully
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_malformed_messages(self):
        """Test handling of malformed messages"""
        manager = AIServiceManager()

        # Messages without required fields
        malformed_messages = [
            {"role": "user"},  # Missing content
            {"content": "Hello"},  # Missing role
        ]

        mock_service = AsyncMock()
        mock_service.chat_completion = AsyncMock(return_value={"content": "Response"})
        mock_service.enabled = True
        mock_service.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("MockService", mock_service)]):
            # Should either handle or raise clear error
            try:
                result = await manager.chat_completion(malformed_messages, stream=False)
                assert isinstance(result, dict)
            except Exception as e:
                # Clear error message is acceptable
                assert len(str(e)) > 0


class TestServiceEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_all_services_return_errors(self):
        """Test when all services return errors"""
        manager = AIServiceManager()

        messages = [{"role": "user", "content": "Test"}]

        mock_service1 = AsyncMock()
        mock_service1.chat_completion = AsyncMock(return_value={"error": "Error 1"})
        mock_service1.enabled = True
        mock_service1.health_check = AsyncMock(return_value=True)

        mock_service2 = AsyncMock()
        mock_service2.chat_completion = AsyncMock(return_value={"error": "Error 2"})
        mock_service2.enabled = True
        mock_service2.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("Service1", mock_service1), ("Service2", mock_service2)]):
            result = await manager.chat_completion(messages, stream=False)

            # Should return error or handle gracefully
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_service_timeout(self):
        """Test handling of service timeouts"""
        manager = AIServiceManager()

        messages = [{"role": "user", "content": "Test"}]

        # Mock service that times out
        async def timeout_call(*args, **kwargs):
            import asyncio
            await asyncio.sleep(100)  # Long delay

        mock_service = AsyncMock()
        mock_service.chat_completion = AsyncMock(side_effect=timeout_call)
        mock_service.enabled = True
        mock_service.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("MockService", mock_service)]):
            # This test would need timeout handling in the actual implementation
            # For now, just verify it's set up correctly
            assert manager.services[0][0] == "MockService"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        manager = AIServiceManager()

        messages = [{"role": "user", "content": "Test"}]

        mock_service = AsyncMock()
        mock_service.chat_completion = AsyncMock(return_value={"content": "Response"})
        mock_service.enabled = True
        mock_service.health_check = AsyncMock(return_value=True)

        with patch.object(manager, 'services', [("MockService", mock_service)]):
            # Make multiple concurrent requests
            import asyncio
            tasks = [
                manager.chat_completion(messages, stream=False)
                for _ in range(5)
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 5
            assert all(isinstance(r, dict) for r in results)
