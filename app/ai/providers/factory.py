"""
AI Provider Factory

根据配置创建对应的AI协议适配器
"""

from enum import Enum

from app.ai.base import BaseAIProvider
from app.ai.exceptions import AIConfigError
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.openai_provider import OpenAIProvider


class AIProviderType(str, Enum):
    """AI协议类型"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIProviderFactory:
    """AI协议适配器工厂"""

    @staticmethod
    def create(
        provider_type: AIProviderType,
        api_key: str,
        base_url: str | None = None,
        default_model: str | None = None,
        **kwargs,
    ) -> BaseAIProvider:
        """创建AI协议适配器"""
        if not api_key:
            raise AIConfigError("API key is required")

        if provider_type == AIProviderType.OPENAI:
            return OpenAIProvider(
                api_key=api_key,
                base_url=base_url or "https://api.openai.com/v1",
                default_model=default_model or "gpt-4-turbo-preview",
                **kwargs,
            )
        elif provider_type == AIProviderType.ANTHROPIC:
            return AnthropicProvider(
                api_key=api_key,
                base_url=base_url or "https://api.anthropic.com/v1",
                default_model=default_model or "claude-3-opus-20240229",
                **kwargs,
            )
        else:
            raise AIConfigError(f"Unknown provider type: {provider_type}")
