"""
Anthropic AI 插件

封装 Anthropic Claude API，实现 AIProviderInterface 接口。
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

from structlog import get_logger

from framework.interfaces.ai_provider import AIProviderInterface

logger = get_logger(__name__)


class AnthropicPlugin(AIProviderInterface):
    """
    Anthropic AI 插件

    支持 Claude 系列模型。
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "claude-3-sonnet-20240229",
        timeout: float = 60.0,
    ):
        """
        初始化 Anthropic 插件

        Args:
            api_key: API 密钥（默认从环境变量 ANTHROPIC_API_KEY 获取）
            default_model: 默认模型
            timeout: 超时时间
        """
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._default_model = default_model
        self._timeout = timeout

    @property
    def name(self) -> str:
        """插件名称"""
        return "anthropic"

    @property
    def supported_models(self) -> list[str]:
        """支持的模型列表"""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]

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
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            AI 回复内容
        """
        import httpx

        model = model or self._default_model

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }

        url = "https://api.anthropic.com/v1/messages"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

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
            model: 模型名称

        Returns:
            分析结果
        """
        import json

        prompt = f"""请分析以下数据并完成任务。

任务: {task}

数据:
{json.dumps(data, ensure_ascii=False, indent=2)}

请以 JSON 格式返回分析结果。"""

        messages = [{"role": "user", "content": prompt}]
        content = await self.chat(messages, model=model)

        # 尝试解析 JSON
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"raw_content": content}

    async def stream_chat(
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
            文本片段
        """
        import httpx

        model = model or self._default_model

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": temperature,
            "stream": True,
        }

        url = "https://api.anthropic.com/v1/messages"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST", url, json=payload, headers=headers
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json

                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            if data.get("delta", {}).get("type") == "text_delta":
                                yield data["delta"]["text"]

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否可用
        """
        try:
            result = await self.chat(
                [{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return len(result) > 0
        except Exception as e:
            logger.warning("anthropic_health_check_failed", error=str(e))
            return False
