"""测试AI提供商接口协议"""

import pytest


class MockAIProvider:
    """模拟AI提供商实现"""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def supported_models(self) -> list[str]:
        return ["gpt-4", "gpt-3.5-turbo"]

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        return "Mock response"

    async def analyze(
        self,
        data: dict,
        task: str,
        model: str | None = None,
    ) -> dict:
        return {"result": "mock"}

    async def health_check(self) -> bool:
        return True


class TestAIProviderInterface:
    """测试AI提供商接口"""

    def test_mock_implementation_satisfies_interface(self):
        """验证模拟实现满足接口"""
        mock = MockAIProvider()

        assert mock.name == "mock"
        assert "gpt-4" in mock.supported_models

    @pytest.mark.asyncio
    async def test_chat_returns_string(self):
        """验证 chat 返回字符串"""
        mock = MockAIProvider()
        response = await mock.chat([{"role": "user", "content": "test"}])
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_analyze_returns_dict(self):
        """验证 analyze 返回字典"""
        mock = MockAIProvider()
        result = await mock.analyze({"data": "test"}, "test task")
        assert isinstance(result, dict)
