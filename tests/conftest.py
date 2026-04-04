"""
Pytest 配置
"""

import pytest
from typing import Generator


@pytest.fixture
def app():
    """FastAPI 应用实例"""
    from app.main import app

    return app


@pytest.fixture
def client(app):
    """测试客户端"""
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """异步测试客户端"""
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
