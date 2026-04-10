"""
API 客户端

调用后端 FastAPI 接口
"""

from typing import Any

import httpx
import streamlit as st

from config import settings


class APIClient:
    """FastAPI 后端客户端"""

    def __init__(self, base_url: str | None = None):
        """
        初始化 API 客户端

        Args:
            base_url: API 基础 URL，默认从配置读取
        """
        self.base_url = base_url or f"http://localhost:{settings.port}"

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        # 从 session state 获取 token（如果有的话）
        if "auth_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        return headers

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
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        POST 请求

        Args:
            endpoint: API 端点
            data: 请求数据

        Returns:
            响应数据
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def put(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        PUT 请求

        Args:
            endpoint: API 端点
            data: 请求数据

        Returns:
            响应数据
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def delete(self, endpoint: str) -> dict[str, Any]:
        """
        DELETE 请求

        Args:
            endpoint: API 端点

        Returns:
            响应数据
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()


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
