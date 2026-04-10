"""
OpenAI Provider 完整测试

使用简单直接的 mock 策略
"""

from unittest.mock import AsyncMock, patch

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


class TestOpenAIProviderAnalyze:
    """OpenAI Provider 分析测试"""

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
                "choices": [{"message": {"content": "Test analysis result"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            },
        ):
            request = AIAnalysisRequest(
                prompt="Test prompt",
                max_tokens=100,
            )
            result = await provider.analyze(request)

            assert result.content == "Test analysis result"
            assert result.model == "gpt-4-turbo-preview"
            assert result.usage is not None
            assert result.usage["total_tokens"] == 30

    @pytest.mark.asyncio
    async def test_analyze_rate_limit(self, provider: OpenAIProvider) -> None:
        """测试限流错误"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            side_effect=AIRateLimitError("Rate limit exceeded"),
        ):
            request = AIAnalysisRequest(prompt="Test")
            with pytest.raises(AIAPIError):  # 重试耗尽后抛出 AIAPIError
                await provider.analyze(request)

    @pytest.mark.asyncio
    async def test_analyze_auth_error(self, provider: OpenAIProvider) -> None:
        """测试认证错误"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            side_effect=AIAPIError("Authentication failed: Invalid API key"),
        ):
            request = AIAnalysisRequest(prompt="Test")
            with pytest.raises(AIAPIError, match="Authentication failed"):
                await provider.analyze(request)

    @pytest.mark.asyncio
    async def test_analyze_model_not_found(self, provider: OpenAIProvider) -> None:
        """测试模型不存在"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            side_effect=AIAPIError("Model not found"),
        ):
            request = AIAnalysisRequest(prompt="Test")
            with pytest.raises(AIAPIError, match="Model not found"):
                await provider.analyze(request)

    @pytest.mark.asyncio
    async def test_analyze_timeout(self, provider: OpenAIProvider) -> None:
        """测试超时"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            side_effect=AITimeoutError("Request timeout after 20.0s"),
        ):
            request = AIAnalysisRequest(prompt="Test")
            with pytest.raises(AIAPIError):  # 重试耗尽
                await provider.analyze(request)

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
    async def test_analyze_with_temperature(self, provider: OpenAIProvider) -> None:
        """测试自定义温度"""
        with patch.object(
            provider,
            "_call_api",
            new_callable=AsyncMock,
            return_value={
                "choices": [{"message": {"content": "result"}}],
                "usage": {"total_tokens": 10},
            },
        ):
            request = AIAnalysisRequest(prompt="Test", temperature=0.5)
            result = await provider.analyze(request)
            assert result.content == "result"


class TestOpenAIProviderTestConnection:
    """OpenAI Provider 连接测试"""

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
            assert result["model"] == "gpt-4"

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

    @pytest.mark.asyncio
    async def test_connection_with_base_url(self, provider: OpenAIProvider) -> None:
        """测试自定义 base_url 连接"""
        mock_result = AsyncMock()
        mock_result.model = "gpt-4"
        mock_result.latency_ms = 150.0

        with patch.object(
            provider, "analyze", new_callable=AsyncMock, return_value=mock_result
        ):
            result = await provider.test_connection()

            assert result["base_url"] == "https://api.openai.com/v1"
