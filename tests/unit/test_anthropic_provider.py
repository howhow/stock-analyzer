"""
Anthropic Provider 完整测试

关键原则: Mock httpx.AsyncClient，让 _call_api 内部代码执行
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.ai.base import AIAnalysisRequest
from app.ai.exceptions import AIAPIError, AIRateLimitError, AITimeoutError
from app.ai.providers.anthropic_provider import AnthropicProvider


class TestAnthropicProviderInit:
    """初始化测试"""

    def test_init_default(self) -> None:
        """测试默认初始化"""
        provider = AnthropicProvider(api_key="test-key")

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.anthropic.com/v1"
        assert provider.default_model == "claude-3-opus-20240229"
        assert provider.timeout == 30.0
        assert provider.max_retries == 3

    def test_init_custom(self) -> None:
        """测试自定义初始化"""
        provider = AnthropicProvider(
            api_key="custom-key",
            base_url="https://custom.api.com/v1",
            default_model="claude-3-sonnet",
            timeout=60.0,
            max_retries=5,
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.api.com/v1"
        assert provider.default_model == "claude-3-sonnet"
        assert provider.timeout == 60.0
        assert provider.max_retries == 5


class TestAnthropicProviderCallAPI:
    """测试 _call_api 内部逻辑 - Mock httpx.AsyncClient"""

    @pytest.fixture
    def provider(self) -> AnthropicProvider:
        return AnthropicProvider(api_key="test-key")

    @pytest.mark.asyncio
    async def test_call_api_success(self, provider: AnthropicProvider) -> None:
        """测试成功调用"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Hello from Claude"}],
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await provider._call_api({"model": "claude-3-opus"})

        assert result["content"][0]["text"] == "Hello from Claude"

    @pytest.mark.asyncio
    async def test_call_api_rate_limit(self, provider: AnthropicProvider) -> None:
        """测试限流错误 (429)"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(AIRateLimitError):
                await provider._call_api({"model": "claude-3-opus"})

    @pytest.mark.asyncio
    async def test_call_api_other_error(self, provider: AnthropicProvider) -> None:
        """测试其他 API 错误"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal error"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(AIAPIError, match="API error 500"):
                await provider._call_api({"model": "claude-3-opus"})

    @pytest.mark.asyncio
    async def test_call_api_timeout(self, provider: AnthropicProvider) -> None:
        """测试超时"""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(AITimeoutError, match="Timeout"):
                await provider._call_api({"model": "claude-3-opus"})


class TestAnthropicProviderAnalyze:
    """测试 analyze 方法"""

    @pytest.fixture
    def provider(self) -> AnthropicProvider:
        return AnthropicProvider(api_key="test-key", max_retries=1)

    @pytest.mark.asyncio
    async def test_analyze_success(self, provider: AnthropicProvider) -> None:
        """测试成功分析"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            return_value={
                "content": [{"text": "Claude response"}],
                "usage": {"input_tokens": 10},
            },
        ):
            request = AIAnalysisRequest(prompt="Test", max_tokens=100)
            result = await provider.analyze(request)

            assert result.content == "Claude response"
            assert result.model == "claude-3-opus-20240229"

    @pytest.mark.asyncio
    async def test_analyze_with_custom_model(self, provider: AnthropicProvider) -> None:
        """测试自定义模型"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            return_value={"content": [{"text": "response"}], "usage": {}},
        ):
            request = AIAnalysisRequest(prompt="Test", model="claude-3-sonnet")
            result = await provider.analyze(request)
            assert result.model == "claude-3-sonnet"

    @pytest.mark.asyncio
    async def test_analyze_rate_limit_retry(self, provider: AnthropicProvider) -> None:
        """测试限流重试"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            side_effect=AIRateLimitError("Rate limit"),
        ):
            request = AIAnalysisRequest(prompt="Test")
            with pytest.raises(AIRateLimitError):
                await provider.analyze(request)


class TestAnthropicProviderTestConnection:
    """测试连接方法"""

    @pytest.fixture
    def provider(self) -> AnthropicProvider:
        return AnthropicProvider(api_key="test-key", max_retries=1)

    @pytest.mark.asyncio
    async def test_connection_success(self, provider: AnthropicProvider) -> None:
        """测试连接成功"""
        mock_result = AsyncMock()
        mock_result.model = "claude-3-opus"

        with patch.object(
            provider, "analyze", new_callable=AsyncMock, return_value=mock_result
        ):
            result = await provider.test_connection()

            assert result["status"] == "connected"
            assert result["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_connection_failed(self, provider: AnthropicProvider) -> None:
        """测试连接失败"""
        with patch.object(
            provider,
            "analyze",
            new_callable=AsyncMock,
            side_effect=Exception("Connection failed"),
        ):
            result = await provider.test_connection()

            assert result["status"] == "failed"
            assert "error" in result
