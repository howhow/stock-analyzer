"""
OpenAI协议适配器

支持OpenAI兼容的API：
- 硅基流动（DeepSeek-V3.2/GLM-4.7/Qwen3）
- 腾讯混元
- 自定义OpenAI兼容API
"""

import asyncio
from typing import Any

import httpx
from structlog import get_logger

from app.ai.base import AIAnalysisRequest, AIAnalysisResponse, BaseAIProvider
from app.ai.exceptions import AIAPIError, AIRateLimitError, AITimeoutError

logger = get_logger(__name__)


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI协议适配器

    支持所有OpenAI兼容的API服务
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4-turbo-preview",
        timeout: float = 20.0,
        max_retries: int = 3,
    ):
        """
        初始化OpenAI协议适配器

        Args:
            api_key: API密钥
            base_url: API基础URL
                - OpenAI: https://api.openai.com/v1
                - 硅基流动: https://api.siliconflow.cn/v1
                - 腾讯混元: https://hunyuan.tencentcloudapi.com/v1
                - 自定义: 用户自定义URL
            default_model: 默认模型
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def analyze(
        self,
        request: AIAnalysisRequest,
    ) -> AIAnalysisResponse:
        """
        执行AI分析

        Args:
            request: 分析请求

        Returns:
            分析响应

        Raises:
            AIAPIError: API调用失败
            AITimeoutError: 超时
            AIRateLimitError: 限流
        """
        import time

        start_time = time.time()
        model = request.model or self.default_model

        logger.info(
            "openai_analyze_started",
            model=model,
            prompt_length=len(request.prompt),
        )

        # 构建请求
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        # 重试逻辑
        last_error: AITimeoutError | AIRateLimitError | None = None
        for attempt in range(self.max_retries):
            try:
                result = await self._call_api(payload)
                latency_ms = (time.time() - start_time) * 1000

                logger.info(
                    "openai_analyze_completed",
                    model=model,
                    latency_ms=latency_ms,
                )

                return AIAnalysisResponse(
                    content=result["choices"][0]["message"]["content"],
                    model=model or self.default_model or "unknown",
                    usage=result.get("usage"),
                    latency_ms=latency_ms,
                )

            except AITimeoutError as e:
                last_error = e
                logger.warning(
                    "openai_timeout_retry",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                )
                await asyncio.sleep(2**attempt)  # 指数退避

            except AIRateLimitError as e:
                last_error = e
                logger.warning(
                    "openai_rate_limit_retry",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                )
                await asyncio.sleep(2**attempt)

            except AIAPIError:
                # API错误不重试
                raise

        # 重试耗尽
        raise AIAPIError(
            f"Failed after {self.max_retries} retries: {last_error}"
        ) from last_error

    async def _call_api(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        调用OpenAI API

        Args:
            payload: 请求载荷

        Returns:
            API响应

        Raises:
            AIAPIError: API错误
            AITimeoutError: 超时
            AIRateLimitError: 限流
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 200:
                    data: dict[str, Any] = response.json()
                    return data

                # 错误处理
                error_data: dict[str, Any] = response.json()
                error_message = error_data.get("error", {}).get(
                    "message", "Unknown error"
                )

                if response.status_code == 429:
                    raise AIRateLimitError(f"Rate limit: {error_message}")
                elif response.status_code == 401:
                    raise AIAPIError(f"Authentication failed: {error_message}")
                elif response.status_code == 404:
                    raise AIAPIError(f"Model not found: {error_message}")
                else:
                    raise AIAPIError(
                        f"API error {response.status_code}: {error_message}"
                    )

        except httpx.TimeoutException as e:
            raise AITimeoutError(f"Request timeout after {self.timeout}s") from e
        except httpx.HTTPError as e:
            raise AIAPIError(f"Network error: {e}") from e

    async def test_connection(self) -> dict[str, Any]:
        """
        测试连接

        Returns:
            连接状态信息
        """
        try:
            # 发送简单请求测试连接
            test_request = AIAnalysisRequest(
                prompt="Hello",
                max_tokens=10,
            )
            response = await self.analyze(test_request)

            return {
                "status": "connected",
                "provider": "openai",
                "base_url": self.base_url,
                "model": response.model,
                "latency_ms": response.latency_ms,
            }

        except Exception as e:
            return {
                "status": "failed",
                "provider": "openai",
                "base_url": self.base_url,
                "error": str(e),
            }
