"""
OpenAI Provider 完整测试

关键原则: 不要 Mock 你想测试的代码！
Mock aiohttp.ClientSession，让 _call_api 内部代码执行
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from app.ai.base import AIAnalysisRequest
from app.ai.exceptions import AIAPIError, AIRateLimitError, AITimeoutError
from app.ai.providers.openai_provider import OpenAIProvider


class TestOpenAIProviderInit:
    """OpenAI Provider 初始化测试"""

    def test_init_default(self) -> None:
        """测试默认初始化"""
        provider = OpenAIProvider(api_key="test-key")

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.default_model == "gpt-4-turbo-preview"
        assert provider.timeout == 20.0
        assert provider.max_retries == 3

    def test_init_custom(self) -> None:
        """测试自定义初始化"""
        provider = OpenAIProvider(
            api_key="custom-key",
            base_url="https://custom.api.com/v1",
            default_model="gpt-4",
            timeout=30.0,
            max_retries=5,
        )

        assert provider.api_key == "custom-key"
        assert provider.base_url == "https://custom.api.com/v1"
        assert provider.default_model == "gpt-4"
        assert provider.timeout == 30.0
        assert provider.max_retries == 5


class TestOpenAIProviderCallAPI:
    """测试 _call_api 内部逻辑 - Mock aiohttp.ClientSession"""

    @pytest.fixture
    def provider(self) -> OpenAIProvider:
        return OpenAIProvider(api_key="test-key")

    @pytest.mark.asyncio
    async def test_call_api_success(self, provider: OpenAIProvider) -> None:
        """测试成功调用 API"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "choices": [{"message": {"content": "OK"}}],
                "usage": {"total_tokens": 100},
            }
        )

        # Mock session - 正确设置异步上下文管理器
        mock_session = AsyncMock()
        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post)

        # Mock ClientSession
        with patch("aiohttp.ClientSession") as mock_client_session:
            mock_client_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await provider._call_api({"model": "gpt-4", "messages": []})

        assert result["choices"][0]["message"]["content"] == "OK"
        assert result["usage"]["total_tokens"] == 100

    @pytest.mark.asyncio
    async def test_call_api_rate_limit(self, provider: OpenAIProvider) -> None:
        """测试限流错误 (429)"""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.json = AsyncMock(
            return_value={"error": {"message": "Rate limit exceeded"}}
        )

        mock_session = AsyncMock()
        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post)

        with patch("aiohttp.ClientSession") as mock_client_session:
            mock_client_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(AIRateLimitError, match="Rate limit"):
                await provider._call_api({"model": "gpt-4"})

    @pytest.mark.asyncio
    async def test_call_api_auth_error(self, provider: OpenAIProvider) -> None:
        """测试认证错误 (401)"""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(
            return_value={"error": {"message": "Invalid API key"}}
        )

        mock_session = AsyncMock()
        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post)

        with patch("aiohttp.ClientSession") as mock_client_session:
            mock_client_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(AIAPIError, match="Authentication failed"):
                await provider._call_api({"model": "gpt-4"})

    @pytest.mark.asyncio
    async def test_call_api_model_not_found(self, provider: OpenAIProvider) -> None:
        """测试模型不存在 (404)"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json = AsyncMock(
            return_value={"error": {"message": "Model not found"}}
        )

        mock_session = AsyncMock()
        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post)

        with patch("aiohttp.ClientSession") as mock_client_session:
            mock_client_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(AIAPIError, match="Model not found"):
                await provider._call_api({"model": "gpt-4"})

    @pytest.mark.asyncio
    async def test_call_api_other_error(self, provider: OpenAIProvider) -> None:
        """测试其他 API 错误 (500)"""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.json = AsyncMock(
            return_value={"error": {"message": "Internal server error"}}
        )

        mock_session = AsyncMock()
        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_post)

        with patch("aiohttp.ClientSession") as mock_client_session:
            mock_client_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(AIAPIError, match="API error 500"):
                await provider._call_api({"model": "gpt-4"})

    @pytest.mark.asyncio
    async def test_call_api_timeout(self, provider: OpenAIProvider) -> None:
        """测试超时"""
        # Mock post 返回一个会抛出 TimeoutError 的上下文管理器
        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_post.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_post)

        with patch("aiohttp.ClientSession") as mock_client_session:
            mock_client_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(AITimeoutError, match="timeout"):
                await provider._call_api({"model": "gpt-4"})

    @pytest.mark.asyncio
    async def test_call_api_network_error(self, provider: OpenAIProvider) -> None:
        """测试网络错误"""
        # Mock post 返回一个会抛出 ClientError 的上下文管理器
        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )
        mock_post.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_post)

        with patch("aiohttp.ClientSession") as mock_client_session:
            mock_client_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(AIAPIError, match="Network error"):
                await provider._call_api({"model": "gpt-4"})


class TestOpenAIProviderAnalyze:
    """测试 analyze 方法 - 使用 _call_api mock"""

    @pytest.fixture
    def provider(self) -> OpenAIProvider:
        return OpenAIProvider(api_key="test-key", max_retries=1)

    @pytest.mark.asyncio
    async def test_analyze_success(self, provider: OpenAIProvider) -> None:
        """测试成功分析"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            return_value={
                "choices": [{"message": {"content": "Test result"}}],
                "usage": {"total_tokens": 50},
            },
        ):
            request = AIAnalysisRequest(prompt="Test", max_tokens=100)
            result = await provider.analyze(request)

            assert result.content == "Test result"
            assert result.model == "gpt-4-turbo-preview"

    @pytest.mark.asyncio
    async def test_analyze_with_custom_model(self, provider: OpenAIProvider) -> None:
        """测试自定义模型"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            return_value={
                "choices": [{"message": {"content": "result"}}],
                "usage": {"total_tokens": 10},
            },
        ):
            request = AIAnalysisRequest(prompt="Test", model="gpt-4-turbo")
            result = await provider.analyze(request)
            assert result.model == "gpt-4-turbo"

    @pytest.mark.asyncio
    async def test_analyze_rate_limit_retry(self, provider: OpenAIProvider) -> None:
        """测试限流重试"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            side_effect=AIRateLimitError("Rate limit"),
        ):
            request = AIAnalysisRequest(prompt="Test")
            with pytest.raises(AIAPIError, match="Failed after"):
                await provider.analyze(request)

    @pytest.mark.asyncio
    async def test_analyze_timeout_retry(self, provider: OpenAIProvider) -> None:
        """测试超时重试"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            side_effect=AITimeoutError("Timeout"),
        ):
            request = AIAnalysisRequest(prompt="Test")
            with pytest.raises(AIAPIError, match="Failed after"):
                await provider.analyze(request)


class TestOpenAIProviderTestConnection:
    """测试连接方法"""

    @pytest.fixture
    def provider(self) -> OpenAIProvider:
        return OpenAIProvider(api_key="test-key", max_retries=1)

    @pytest.mark.asyncio
    async def test_connection_success(self, provider: OpenAIProvider) -> None:
        """测试连接成功"""
        mock_result = AsyncMock()
        mock_result.model = "gpt-4"
        mock_result.latency_ms = 100.0

        with patch.object(
            provider, "analyze", new_callable=AsyncMock, return_value=mock_result
        ):
            result = await provider.test_connection()

            assert result["status"] == "connected"
            assert result["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_connection_failed(self, provider: OpenAIProvider) -> None:
        """测试连接失败"""
        with patch.object(
            provider,
            "analyze",
            new_callable=AsyncMock,
            side_effect=Exception("Connection refused"),
        ):
            result = await provider.test_connection()

            assert result["status"] == "failed"
            assert "error" in result
