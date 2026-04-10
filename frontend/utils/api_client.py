"""
API 客户端

调用后端 FastAPI 接口，支持超时配置和重试机制
"""

import asyncio
import logging
from typing import Any

import httpx
import streamlit as st

from config import settings

logger = logging.getLogger(__name__)


class APIError(Exception):
    """API 调用错误"""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class APIClient:
    """FastAPI 后端客户端"""

    def __init__(self, base_url: str | None = None):
        """
        初始化 API 客户端

        Args:
            base_url: API 基础 URL，默认从配置读取
        """
        self.base_url = base_url or f"http://localhost:{settings.port}"
        self.timeout = settings.api_timeout
        self.max_retries = settings.api_max_retries
        self.retry_delay = settings.api_retry_delay

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        # 从 session state 获取 token（如果有的话）
        if "auth_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        return headers

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        带重试的请求方法

        Args:
            method: HTTP 方法
            url: 请求 URL
            **kwargs: 其他请求参数

        Returns:
            响应数据

        Raises:
            APIError: 请求失败
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method,
                        url,
                        headers=self._get_headers(),
                        timeout=self.timeout,
                        **kwargs,
                    )
                    response.raise_for_status()
                    result: dict[str, Any] = response.json()
                    return result

            except httpx.TimeoutException as e:
                last_error = APIError(
                    f"请求超时 (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                logger.warning(
                    f"API request timeout (attempt {attempt + 1}/{self.max_retries}): "
                    f"{method} {url} - {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

            except httpx.HTTPStatusError as e:
                # 4xx 错误不重试
                if 400 <= e.response.status_code < 500:
                    logger.error(
                        f"API client error: {method} {url} - "
                        f"{e.response.status_code}"
                    )
                    raise APIError(
                        f"客户端错误: {e.response.status_code} - " f"{e.response.text}",
                        status_code=e.response.status_code,
                    ) from e
                # 5xx 错误重试
                last_error = APIError(
                    f"服务器错误 (attempt {attempt + 1}/"
                    f"{self.max_retries}): {e.response.status_code}",
                    status_code=e.response.status_code,
                )
                logger.warning(
                    f"API server error (attempt {attempt + 1}/{self.max_retries}): "
                    f"{method} {url} - {e.response.status_code}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

            except httpx.RequestError as e:
                last_error = APIError(f"网络错误: {e}")
                logger.warning(
                    f"API network error (attempt {attempt + 1}/{self.max_retries}): "
                    f"{method} {url} - {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        raise last_error or APIError("未知错误")

    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        GET 请求

        Args:
            endpoint: API 端点
            params: 查询参数

        Returns:
            响应数据
        """
        return await self._request_with_retry(
            "GET",
            f"{self.base_url}{endpoint}",
            params=params,
        )

    async def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        POST 请求

        Args:
            endpoint: API 端点
            data: 请求数据

        Returns:
            响应数据
        """
        return await self._request_with_retry(
            "POST",
            f"{self.base_url}{endpoint}",
            json=data,
        )

    async def put(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        PUT 请求

        Args:
            endpoint: API 端点
            data: 请求数据

        Returns:
            响应数据
        """
        return await self._request_with_retry(
            "PUT",
            f"{self.base_url}{endpoint}",
            json=data,
        )

    async def delete(self, endpoint: str) -> dict[str, Any]:
        """
        DELETE 请求

        Args:
            endpoint: API 端点

        Returns:
            响应数据
        """
        return await self._request_with_retry(
            "DELETE",
            f"{self.base_url}{endpoint}",
        )


# 全局客户端实例
_api_client: APIClient | None = None


def get_api_client() -> APIClient:
    """
    获取 API 客户端单例

    Returns:
        APIClient 实例
    """
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client
