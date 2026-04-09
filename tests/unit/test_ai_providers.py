"""
AI协议适配器测试

测试OpenAI和Anthropic协议适配器
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.base import AIAnalysisRequest
from app.ai.exceptions import AIConfigError
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.factory import AIProviderFactory, AIProviderType
from app.ai.providers.openai_provider import OpenAIProvider


class TestAIProviderFactory:
    """测试AI协议适配器工厂"""

    def test_create_openai_provider(self):
        """测试创建OpenAI适配器"""
        provider = AIProviderFactory.create(
            provider_type=AIProviderType.OPENAI,
            api_key="test-key",
        )
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-key"

    def test_create_anthropic_provider(self):
        """测试创建Anthropic适配器"""
        provider = AIProviderFactory.create(
            provider_type=AIProviderType.ANTHROPIC,
            api_key="test-key",
        )
        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == "test-key"

    def test_create_provider_without_api_key(self):
        """测试缺少API Key"""
        with pytest.raises(AIConfigError):
            AIProviderFactory.create(
                provider_type=AIProviderType.OPENAI,
                api_key="",
            )

    def test_create_provider_with_custom_url(self):
        """测试自定义URL"""
        provider = AIProviderFactory.create(
            provider_type=AIProviderType.OPENAI,
            api_key="test-key",
            base_url="https://custom.api.com/v1",
        )
        assert provider.base_url == "https://custom.api.com/v1"


class TestOpenAIProvider:
    """测试OpenAI适配器"""

    @pytest.fixture
    def provider(self):
        """创建测试用的OpenAI适配器"""
        return OpenAIProvider(
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            default_model="gpt-4-turbo-preview",
        )

    @pytest.mark.asyncio
    async def test_analyze_success(self, provider):
        """测试成功分析"""
        mock_response = {
            "choices": [{"message": {"content": "测试响应"}}],
            "usage": {"total_tokens": 100},
        }

        # Mock the _call_api method directly
        with patch.object(provider, "_call_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            request = AIAnalysisRequest(prompt="测试提示")
            response = await provider.analyze(request)

            assert response.content == "测试响应"
            assert response.model == "gpt-4-turbo-preview"

    @pytest.mark.asyncio
    async def test_test_connection(self, provider):
        """测试连接测试"""
        with patch.object(provider, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = MagicMock(
                model="gpt-4-turbo-preview",
                latency_ms=100.0,
            )

            result = await provider.test_connection()

            assert result["status"] == "connected"
            assert result["provider"] == "openai"


class TestAnthropicProvider:
    """测试Anthropic适配器"""

    @pytest.fixture
    def provider(self):
        """创建测试用的Anthropic适配器"""
        return AnthropicProvider(
            api_key="test-key",
            base_url="https://api.anthropic.com/v1",
            default_model="claude-3-opus-20240229",
        )

    @pytest.mark.asyncio
    async def test_analyze_success(self, provider):
        """测试成功分析"""
        mock_response = {
            "content": [{"text": "Claude响应"}],
            "usage": {"total_tokens": 100},
        }

        # Mock the _call_api method directly
        with patch.object(provider, "_call_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            request = AIAnalysisRequest(prompt="测试提示")
            response = await provider.analyze(request)

            assert response.content == "Claude响应"
            assert response.model == "claude-3-opus-20240229"

    @pytest.mark.asyncio
    async def test_test_connection(self, provider):
        """测试连接测试"""
        with patch.object(provider, "analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = MagicMock(
                model="claude-3-opus-20240229",
            )

            result = await provider.test_connection()

            assert result["status"] == "connected"
            assert result["provider"] == "anthropic"
