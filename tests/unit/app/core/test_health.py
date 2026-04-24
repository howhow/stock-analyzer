import pytest

"""
健康检查 API 测试
"""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """测试健康检查接口"""
    from app.api.paths import API_HEALTH
    response = client.get(API_HEALTH)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_readiness_check(client: TestClient):
    """测试就绪检查接口"""
    from app.api.paths import API_READY
    response = client.get(API_READY)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data


def test_root_endpoint(client: TestClient):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
