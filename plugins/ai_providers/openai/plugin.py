"""
OpenAI AI 插件

封装 OpenAI API，实现 AIProviderInterface 接口。
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

from structlog import get_logger

from framework.interfaces.ai_provider import AIProviderInterface

logger = get_logger(__name__)


class OpenAIPlugin(AIProviderInterface):
    """
    OpenAI AI 插件

    支持所有 OpenAI 兼容的 API 服务。
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4-turbo-preview",
        timeout: float = 30.0,
    ):
        """
        初始化 OpenAI 插件

        Args:
            api_key: API 密钥（默认从环境变量 OPENAI_API_KEY 获取）
            base_url: API 基础 URL
            default_model: 默认模型
            timeout: 超时时间
        """
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._base_url = base_url or os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        self._default_model = default_model
        self._timeout = timeout
        self._client: Any = None

    @property
    def name(self) -> str:
        """插件名称"""
        return "openai"

    @property
    def supported_models(self) -> list[str]:
        """支持的模型列表"""
        return [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
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
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        url = f"{self._base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            content: str = data["choices"][0]["message"]["content"]
            return content

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
            # 提取 JSON 块
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            result: dict[str, Any] = json.loads(json_str)
            return result
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
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        url = f"{self._base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST", url, json=payload, headers=headers
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        import json

                        chunk = json.loads(data)
                        if chunk["choices"][0]["delta"].get("content"):
                            yield chunk["choices"][0]["delta"]["content"]

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否可用
        """
        try:
            # 发送简单请求测试
            result = await self.chat(
                [{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return len(result) > 0
        except Exception as e:
            logger.warning("openai_health_check_failed", error=str(e))
            return False
