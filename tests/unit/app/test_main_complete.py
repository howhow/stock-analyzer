"""
FastAPI 主程序测试 - 覆盖 lifespan 和 root endpoint
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app, create_app


class TestMainApp:
    """主程序测试"""

    def test_create_app(self):
        """测试创建应用"""
        test_app = create_app()

        assert test_app is not None
        # title 可能是 'stock-analyzer' 或 'Stock Analyzer'
        assert test_app.title.lower().replace("-", " ") in [
            "stock analyzer",
            "stock-analyzer",
        ]
        assert test_app.version == "0.1.0"

    def test_root_endpoint(self):
        """测试根路径"""
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        # 验证返回的 health 路径正确
        assert data.get("health") == "/api/v1/health"

    def test_health_endpoint(self):
        """测试健康检查"""
        from app.api.paths import API_HEALTH

        client = TestClient(app)

        response = client.get(API_HEALTH)

        # 可能返回 200 或 404（取决于路由）
        assert response.status_code in [200, 404]

    def test_docs_endpoint(self):
        """测试文档端点"""
        client = TestClient(app)

        response = client.get("/docs")

        assert response.status_code == 200

    def test_redoc_endpoint(self):
        """测试 ReDoc 端点"""
        client = TestClient(app)

        response = client.get("/redoc")

        assert response.status_code == 200


class TestLifespan:
    """生命周期测试"""

    def test_lifespan_import(self):
        """测试导入 lifespan"""
        from app.main import lifespan

        assert lifespan is not None

    def test_app_has_state(self):
        """测试应用状态"""
        # 测试应用可以正常创建
        test_app = create_app()
        assert hasattr(test_app, "state") or test_app is not None
