"""
AI提供商接口协议

定义所有AI提供商插件必须实现的接口。
"""

from typing import Any, AsyncIterator, Protocol, runtime_checkable


@runtime_checkable
class AIProviderInterface(Protocol):
    """
    AI提供商接口协议

    所有AI提供商（OpenAI、Claude、DeepSeek等）必须实现此接口。
    """

    @property
    def name(self) -> str:
        """
        提供商名称

        Returns:
            提供商名称（如 'openai', 'anthropic', 'deepseek'）
        """
        ...

    @property
    def supported_models(self) -> list[str]:
        """
        支持的模型列表

        Returns:
            模型名称列表
        """
        ...

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """
        对话接口

        Args:
            messages: 消息列表（[{'role': 'user', 'content': '...'}]）
            model: 模型名称（可选，使用默认模型）
            temperature: 温度参数（0-1）
            max_tokens: 最大token数（可选）

        Returns:
            AI回复内容

        Raises:
            AIError: AI调用失败
            AIQuotaExceededError: 配额超限
        """
        ...

    async def analyze(
        self,
        data: dict[str, Any],
        task: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        分析接口

        Args:
            data: 待分析数据
            task: 分析任务描述
            model: 模型名称（可选）

        Returns:
            分析结果

        Raises:
            AIError: AI分析失败
        """
        ...

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        流式对话接口

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数

        Yields:
            str: 流式输出的文本片段
        """
        ...

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True 如果提供商可用，False 否则
        """
        ...
