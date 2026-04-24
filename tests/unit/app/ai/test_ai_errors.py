"""
AI Provider错误处理测试

测试AI provider的错误场景
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.ai.base import AIAnalysisRequest
from app.ai.exceptions import AIAPIError, AIRateLimitError, AITimeoutError
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.openai_provider import OpenAIProvider


class TestOpenAIProviderErrors:
    """测试OpenAI适配器错误处理"""

    @pytest.fixture
    def provider(self):
        return OpenAIProvider(api_key="test-key", max_retries=2)

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, provider):
        """测试限流错误"""
        with patch.object(provider, "_call_api", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = AIRateLimitError("Rate limit exceeded")

            request = AIAnalysisRequest(prompt="test")
            with pytest.raises(AIAPIError) as exc_info:
                await provider.analyze(request)

            assert "Failed after 2 retries" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_error(self, provider):
        """测试超时错误"""
        with patch.object(provider, "_call_api", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = AITimeoutError("Timeout")

            request = AIAnalysisRequest(prompt="test")
            with pytest.raises(AIAPIError):
                await provider.analyze(request)


class TestAnthropicProviderErrors:
    """测试Anthropic适配器错误处理"""

    @pytest.fixture
    def provider(self):
        return AnthropicProvider(api_key="test-key", max_retries=2)

    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, provider):
        """测试限流重试"""
        with patch.object(provider, "_call_api", new_callable=AsyncMock) as mock_call:
            # 第一次限流，第二次成功
            mock_call.side_effect = [
                AIRateLimitError("Rate limit"),
                {"content": [{"text": "Success"}], "usage": {}},
            ]

            request = AIAnalysisRequest(prompt="test")
            response = await provider.analyze(request)

            assert response.content == "Success"
            assert mock_call.call_count == 2
