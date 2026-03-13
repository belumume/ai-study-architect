"""
Comprehensive tests for AIServiceManager.

Covers: initialization, service selection, fallback logic, chat_completion
(including preferred service, streaming, error propagation), and
analyze_content with all branch paths.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai_service_manager import AIServiceManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_service(
    *,
    enabled: bool = True,
    healthy: bool = True,
    has_health_check: bool = True,
    has_analyze: bool = False,
    chat_return=None,
    chat_side_effect=None,
    analyze_return=None,
):
    """Build a mock AI service with configurable attributes."""
    svc = MagicMock()

    # `enabled` is checked via hasattr + property access
    svc.enabled = enabled

    if has_health_check:
        svc.health_check = AsyncMock(return_value=healthy)
    else:
        # Remove attribute so hasattr returns False
        del svc.health_check

    chat_ret = chat_return if chat_return is not None else {"response": "ok"}
    svc.chat_completion = AsyncMock(return_value=chat_ret, side_effect=chat_side_effect)

    if has_analyze:
        analyze_ret = (
            analyze_return
            if analyze_return is not None
            else {
                "summary": "analysis done",
                "key_concepts": ["concept1"],
            }
        )
        svc.analyze_content = AsyncMock(return_value=analyze_ret)
    else:
        if hasattr(svc, "analyze_content"):
            del svc.analyze_content

    return svc


def _manager_with(services):
    """Create an AIServiceManager with injected service list."""
    mgr = AIServiceManager.__new__(AIServiceManager)
    mgr.services = services
    return mgr


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInitialization:
    """Test AIServiceManager constructor."""

    def test_services_list_contains_two_entries(self):
        manager = AIServiceManager()
        assert len(manager.services) == 2

    def test_claude_is_primary(self):
        manager = AIServiceManager()
        assert manager.services[0][0] == "Claude"

    def test_openai_is_fallback(self):
        manager = AIServiceManager()
        assert manager.services[1][0] == "OpenAI"

    def test_service_entries_are_name_instance_tuples(self):
        manager = AIServiceManager()
        for name, service in manager.services:
            assert isinstance(name, str)
            assert hasattr(service, "chat_completion")


# ---------------------------------------------------------------------------
# get_available_service
# ---------------------------------------------------------------------------


class TestGetAvailableService:
    """Test service selection and fallback in get_available_service."""

    async def test_returns_first_healthy_service(self):
        svc = _make_mock_service(enabled=True, healthy=True)
        mgr = _manager_with([("Primary", svc)])

        name, service = await mgr.get_available_service()

        assert name == "Primary"
        assert service is svc
        svc.health_check.assert_awaited_once()

    async def test_skips_disabled_service(self):
        disabled = _make_mock_service(enabled=False)
        enabled = _make_mock_service(enabled=True, healthy=True)
        mgr = _manager_with([("Disabled", disabled), ("Enabled", enabled)])

        name, service = await mgr.get_available_service()

        assert name == "Enabled"
        assert service is enabled

    async def test_skips_unhealthy_falls_to_next(self):
        unhealthy = _make_mock_service(enabled=True, healthy=False)
        healthy = _make_mock_service(enabled=True, healthy=True)
        mgr = _manager_with([("Sick", unhealthy), ("Good", healthy)])

        name, service = await mgr.get_available_service()

        assert name == "Good"
        assert service is healthy

    async def test_returns_none_when_all_disabled(self):
        d1 = _make_mock_service(enabled=False)
        d2 = _make_mock_service(enabled=False)
        mgr = _manager_with([("A", d1), ("B", d2)])

        name, service = await mgr.get_available_service()

        assert name is None
        assert service is None

    async def test_returns_none_when_all_unhealthy(self):
        s1 = _make_mock_service(enabled=True, healthy=False)
        s2 = _make_mock_service(enabled=True, healthy=False)
        mgr = _manager_with([("A", s1), ("B", s2)])

        name, service = await mgr.get_available_service()

        assert name is None
        assert service is None

    async def test_health_check_exception_skips_to_next(self):
        broken = _make_mock_service(enabled=True, healthy=True)
        broken.health_check = AsyncMock(side_effect=RuntimeError("connection timeout"))
        good = _make_mock_service(enabled=True, healthy=True)
        mgr = _manager_with([("Broken", broken), ("Good", good)])

        name, service = await mgr.get_available_service()

        assert name == "Good"

    async def test_service_without_health_check_uses_enabled(self):
        """If a service has no health_check method but is enabled, use it."""
        svc = _make_mock_service(enabled=True, has_health_check=False)
        mgr = _manager_with([("NoHC", svc)])

        name, service = await mgr.get_available_service()

        assert name == "NoHC"
        assert service is svc

    async def test_service_without_health_check_but_disabled(self):
        """Service without health_check AND disabled should be skipped."""
        svc = _make_mock_service(enabled=False, has_health_check=False)
        mgr = _manager_with([("NoHC", svc)])

        name, service = await mgr.get_available_service()

        assert name is None
        assert service is None

    async def test_disabled_service_with_api_key_logs_warning(self, caplog):
        """When service is disabled but env has API key, log a warning."""
        svc = _make_mock_service(enabled=False)
        mgr = _manager_with([("Claude", svc)])

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-fake-key"}):
            import logging

            with caplog.at_level(logging.WARNING):
                name, _ = await mgr.get_available_service()

        assert name is None
        assert "has API key but reports not enabled" in caplog.text

    async def test_disabled_service_without_api_key_no_warning(self, caplog):
        """When service is disabled and no env key, should log debug, not warning."""
        svc = _make_mock_service(enabled=False)
        mgr = _manager_with([("Claude", svc)])

        env_patch = {"ANTHROPIC_API_KEY": "", "CLAUDE_API_KEY": ""}
        with patch.dict(os.environ, env_patch, clear=False):
            import logging

            with caplog.at_level(logging.DEBUG):
                name, _ = await mgr.get_available_service()

        assert name is None
        assert "has API key but reports not enabled" not in caplog.text


# ---------------------------------------------------------------------------
# chat_completion -- priority order (no prefer_service)
# ---------------------------------------------------------------------------


class TestChatCompletionPriorityOrder:
    """Test chat_completion when no prefer_service is specified."""

    async def test_uses_first_enabled_service(self):
        svc = _make_mock_service(chat_return={"response": "Hello from primary"})
        mgr = _manager_with([("Primary", svc)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["response"] == "Hello from primary"
        svc.chat_completion.assert_awaited_once()

    async def test_skips_disabled_service_in_fallback(self):
        disabled = _make_mock_service(enabled=False)
        enabled = _make_mock_service(chat_return={"response": "from fallback"})
        mgr = _manager_with([("Disabled", disabled), ("Enabled", enabled)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["response"] == "from fallback"
        disabled.chat_completion.assert_not_awaited()
        enabled.chat_completion.assert_awaited_once()

    async def test_skips_service_returning_error(self):
        erroring = _make_mock_service(chat_return={"error": "rate limit", "response": "try again"})
        good = _make_mock_service(chat_return={"response": "success"})
        mgr = _manager_with([("Erroring", erroring), ("Good", good)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["response"] == "success"
        assert "error" not in result

    async def test_skips_service_raising_exception(self):
        broken = _make_mock_service(chat_side_effect=ConnectionError("network down"))
        good = _make_mock_service(chat_return={"response": "recovered"})
        mgr = _manager_with([("Broken", broken), ("Good", good)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["response"] == "recovered"

    async def test_all_fail_returns_error_dict(self):
        s1 = _make_mock_service(chat_side_effect=Exception("fail 1"))
        s2 = _make_mock_service(chat_return={"error": "fail 2"})
        mgr = _manager_with([("S1", s1), ("S2", s2)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["error"] == "All AI services unavailable"
        assert "try again later" in result["response"]

    async def test_passes_temperature_and_max_tokens(self):
        svc = _make_mock_service(chat_return={"response": "ok"})
        mgr = _manager_with([("Svc", svc)])

        await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            temperature=0.2,
            max_tokens=500,
            stream=False,
        )

        call_kwargs = svc.chat_completion.call_args[1]
        assert call_kwargs["temperature"] == 0.2
        assert call_kwargs["max_tokens"] == 500

    async def test_passes_stream_flag(self):
        async def mock_stream():
            yield '{"response": "chunk", "done": false}'

        svc = _make_mock_service(chat_return=mock_stream())
        mgr = _manager_with([("Svc", svc)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=True,
        )

        call_kwargs = svc.chat_completion.call_args[1]
        assert call_kwargs["stream"] is True
        # Streaming result is returned directly (generator, not dict)
        assert result is not None

    async def test_empty_services_list(self):
        mgr = _manager_with([])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["error"] == "All AI services unavailable"


# ---------------------------------------------------------------------------
# chat_completion -- prefer_service
# ---------------------------------------------------------------------------


class TestChatCompletionPreferService:
    """Test the prefer_service parameter."""

    async def test_uses_preferred_service_when_available(self):
        primary = _make_mock_service(chat_return={"response": "from primary"})
        preferred = _make_mock_service(chat_return={"response": "from preferred"})
        mgr = _manager_with([("Primary", primary), ("Preferred", preferred)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            prefer_service="Preferred",
            stream=False,
        )

        assert result["response"] == "from preferred"
        preferred.chat_completion.assert_awaited_once()
        # Primary should NOT have been called because preferred succeeded
        primary.chat_completion.assert_not_awaited()

    async def test_prefer_service_case_insensitive(self):
        svc = _make_mock_service(chat_return={"response": "found it"})
        mgr = _manager_with([("Claude", svc)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            prefer_service="claude",
            stream=False,
        )

        assert result["response"] == "found it"

    async def test_preferred_fails_falls_back_to_priority_order(self):
        preferred = _make_mock_service(chat_side_effect=Exception("preferred down"))
        fallback = _make_mock_service(chat_return={"response": "fallback saved us"})
        mgr = _manager_with([("Fallback", fallback), ("Preferred", preferred)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            prefer_service="Preferred",
            stream=False,
        )

        assert result["response"] == "fallback saved us"

    async def test_preferred_returns_error_falls_back(self):
        preferred = _make_mock_service(chat_return={"error": "overloaded", "response": "try later"})
        fallback = _make_mock_service(chat_return={"response": "from fallback"})
        mgr = _manager_with([("Fallback", fallback), ("Preferred", preferred)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            prefer_service="Preferred",
            stream=False,
        )

        assert result["response"] == "from fallback"

    async def test_nonexistent_preferred_uses_priority_order(self):
        svc = _make_mock_service(chat_return={"response": "normal flow"})
        mgr = _manager_with([("Claude", svc)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            prefer_service="NonexistentService",
            stream=False,
        )

        assert result["response"] == "normal flow"

    async def test_preferred_streaming_returns_generator_directly(self):
        async def mock_stream():
            yield '{"response": "chunk1", "done": false}'
            yield '{"response": "chunk2", "done": true}'

        gen = mock_stream()
        svc = _make_mock_service(chat_return=gen)
        mgr = _manager_with([("Svc", svc)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            prefer_service="Svc",
            stream=True,
        )

        # Streaming returns the generator directly, not a dict
        assert result is gen


# ---------------------------------------------------------------------------
# analyze_content
# ---------------------------------------------------------------------------


class TestAnalyzeContent:
    """Test the analyze_content method."""

    async def test_returns_analysis_from_first_capable_service(self):
        analysis = {
            "summary": "Great content",
            "key_concepts": ["recursion", "base case"],
        }
        svc = _make_mock_service(
            enabled=True,
            has_analyze=True,
            analyze_return=analysis,
        )
        mgr = _manager_with([("Claude", svc)])

        result = await mgr.analyze_content(
            content="def factorial(n): ...",
            content_type="python",
        )

        assert result["summary"] == "Great content"
        assert result["key_concepts"] == ["recursion", "base case"]
        svc.analyze_content.assert_awaited_once_with("def factorial(n): ...", "python", None)

    async def test_passes_instructions_to_service(self):
        svc = _make_mock_service(
            enabled=True,
            has_analyze=True,
            analyze_return={"summary": "ok", "key_concepts": []},
        )
        mgr = _manager_with([("Claude", svc)])

        await mgr.analyze_content(
            content="text",
            content_type="markdown",
            instructions="Focus on algorithms",
        )

        svc.analyze_content.assert_awaited_once_with("text", "markdown", "Focus on algorithms")

    async def test_skips_service_without_analyze_content_method(self):
        no_analyze = _make_mock_service(enabled=True, has_analyze=False)
        with_analyze = _make_mock_service(
            enabled=True,
            has_analyze=True,
            analyze_return={"summary": "analyzed", "key_concepts": ["x"]},
        )
        mgr = _manager_with([("NoAnalyze", no_analyze), ("HasAnalyze", with_analyze)])

        result = await mgr.analyze_content(content="text", content_type="pdf")

        assert result["summary"] == "analyzed"

    async def test_skips_disabled_service(self):
        disabled = _make_mock_service(enabled=False, has_analyze=True)
        enabled = _make_mock_service(
            enabled=True,
            has_analyze=True,
            analyze_return={"summary": "from enabled", "key_concepts": []},
        )
        mgr = _manager_with([("Disabled", disabled), ("Enabled", enabled)])

        result = await mgr.analyze_content(content="text", content_type="txt")

        assert result["summary"] == "from enabled"
        disabled.analyze_content.assert_not_awaited()

    async def test_skips_service_returning_error(self):
        erroring = _make_mock_service(
            enabled=True,
            has_analyze=True,
            analyze_return={"error": "overloaded", "summary": "fail"},
        )
        good = _make_mock_service(
            enabled=True,
            has_analyze=True,
            analyze_return={"summary": "good analysis", "key_concepts": ["a"]},
        )
        mgr = _manager_with([("Erroring", erroring), ("Good", good)])

        result = await mgr.analyze_content(content="text", content_type="pdf")

        assert result["summary"] == "good analysis"

    async def test_skips_service_raising_exception(self):
        broken = _make_mock_service(enabled=True, has_analyze=True)
        broken.analyze_content = AsyncMock(side_effect=RuntimeError("boom"))
        good = _make_mock_service(
            enabled=True,
            has_analyze=True,
            analyze_return={"summary": "recovered", "key_concepts": []},
        )
        mgr = _manager_with([("Broken", broken), ("Good", good)])

        result = await mgr.analyze_content(content="text", content_type="pdf")

        assert result["summary"] == "recovered"

    async def test_all_fail_returns_fallback_error(self):
        broken = _make_mock_service(enabled=True, has_analyze=True)
        broken.analyze_content = AsyncMock(side_effect=Exception("fail"))
        mgr = _manager_with([("Broken", broken)])

        result = await mgr.analyze_content(content="text", content_type="pdf")

        assert result["error"] == "Content analysis failed"
        assert result["summary"] == "Unable to analyze content"
        assert result["key_concepts"] == []

    async def test_no_services_returns_fallback_error(self):
        mgr = _manager_with([])

        result = await mgr.analyze_content(content="text", content_type="pdf")

        assert result["error"] == "Content analysis failed"

    async def test_service_without_enabled_attr_is_skipped(self):
        """Service missing both 'enabled' attr and 'analyze_content' is skipped."""
        svc = MagicMock(spec=[])  # Empty spec -- no attributes
        mgr = _manager_with([("Empty", svc)])

        result = await mgr.analyze_content(content="text", content_type="pdf")

        assert result["error"] == "Content analysis failed"


# ---------------------------------------------------------------------------
# chat_completion -- streaming edge cases
# ---------------------------------------------------------------------------


class TestChatCompletionStreaming:
    """Test streaming-specific behavior in chat_completion."""

    async def test_streaming_via_prefer_service_returns_generator(self):
        """The prefer_service path has an early `if stream: return result`
        that correctly returns an async generator before error checking."""

        async def mock_stream():
            yield '{"response": "streaming", "done": false}'

        gen = mock_stream()
        svc = _make_mock_service(chat_return=gen)
        mgr = _manager_with([("Svc", svc)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            prefer_service="Svc",
            stream=True,
        )

        assert result is gen

    async def test_streaming_fallback_path_fails_because_generator_has_no_get(self):
        """BUG documentation: The fallback (non-prefer) path calls
        result.get('error') on an async generator, causing AttributeError
        which is caught and the service is skipped. Streaming only works
        reliably via the prefer_service path."""

        async def mock_stream():
            yield '{"response": "from fallback", "done": true}'

        gen = mock_stream()
        enabled = _make_mock_service(chat_return=gen)
        mgr = _manager_with([("Svc", enabled)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=True,
        )

        # Falls through to "All AI services unavailable" because the
        # generator doesn't have .get() and the AttributeError is caught
        assert result["error"] == "All AI services unavailable"


# ---------------------------------------------------------------------------
# chat_completion -- all services exhausted
# ---------------------------------------------------------------------------


class TestChatCompletionAllFail:
    """Test the 'all services failed' code path."""

    async def test_all_disabled_returns_unavailable(self):
        d1 = _make_mock_service(enabled=False)
        d2 = _make_mock_service(enabled=False)
        mgr = _manager_with([("A", d1), ("B", d2)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["error"] == "All AI services unavailable"
        assert "try again later" in result["response"]

    async def test_all_exception_returns_unavailable(self):
        s1 = _make_mock_service(chat_side_effect=TimeoutError("timeout"))
        s2 = _make_mock_service(chat_side_effect=ConnectionError("refused"))
        mgr = _manager_with([("S1", s1), ("S2", s2)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["error"] == "All AI services unavailable"

    async def test_all_error_responses_returns_unavailable(self):
        s1 = _make_mock_service(chat_return={"error": "quota exceeded"})
        s2 = _make_mock_service(chat_return={"error": "model overloaded"})
        mgr = _manager_with([("S1", s1), ("S2", s2)])

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["error"] == "All AI services unavailable"

    async def test_mix_of_disabled_erroring_and_exception(self):
        disabled = _make_mock_service(enabled=False)
        erroring = _make_mock_service(chat_return={"error": "bad request"})
        broken = _make_mock_service(chat_side_effect=Exception("crash"))
        mgr = _manager_with(
            [
                ("Disabled", disabled),
                ("Erroring", erroring),
                ("Broken", broken),
            ]
        )

        result = await mgr.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        assert result["error"] == "All AI services unavailable"


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------


class TestGlobalInstance:
    """Test the module-level singleton."""

    def test_global_instance_exists(self):
        from app.services.ai_service_manager import ai_service_manager

        assert isinstance(ai_service_manager, AIServiceManager)

    def test_global_instance_has_services(self):
        from app.services.ai_service_manager import ai_service_manager

        assert len(ai_service_manager.services) == 2
