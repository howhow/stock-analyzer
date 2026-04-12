"""
Anthropic协议适配器

支持Claude系列模型
"""

import asyncio
import time
from typing import Any

import httpx
from structlog import get_logger

from app.ai.base import AIAnalysisRequest, AIAnalysisResponse, BaseAIProvider
from app.ai.exceptions import AIAPIError, AIRateLimitError, AITimeoutError

logger = get_logger(__name__)


class AnthropicProvider(BaseAIProvider):
    """Anthropic协议适配器"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com/v1",
        default_model: str = "claude-3-opus-20240229",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def analyze(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        start_time = time.time()
        model = request.model or self.default_model

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
        }

        for attempt in range(self.max_retries):
            try:
                result = await self._call_api(payload)
                latency_ms = (time.time() - start_time) * 1000

                return AIAnalysisResponse(
                    content=result["content"][0]["text"],
                    model=model or self.default_model or "unknown",
                    usage=result.get("usage"),
                    latency_ms=latency_ms,
                )
            except (AITimeoutError, AIRateLimitError):
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                else:
                    raise

        raise AIAPIError("Unexpected error")

    async def _call_api(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/messages"

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

                error: dict[str, Any] = response.json()
                if response.status_code == 429:
                    raise AIRateLimitError(str(error))
                raise AIAPIError(f"API error {response.status_code}: {error}")

        except httpx.TimeoutException as e:
            raise AITimeoutError(f"Timeout after {self.timeout}s") from e

    async def test_connection(self) -> dict[str, Any]:
        try:
            response = await self.analyze(AIAnalysisRequest(prompt="Hi", max_tokens=10))
            return {
                "status": "connected",
                "provider": "anthropic",
                "model": response.model,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
