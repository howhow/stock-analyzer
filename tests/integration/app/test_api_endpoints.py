"""API 端点集成测试 — 端到端验证"""

import pytest


@pytest.mark.integration
class TestAPIEndpointsIntegration:
    """API 端点端到端集成测试"""

    def test_api_health_check(self, api_service):
        """验证 API 健康检查端点"""
        import requests

        port = api_service["port"]

        # 测试 API 健康检查
        response = requests.get(f"http://localhost:{port}/api/v1/health", timeout=2)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ok", "healthy"]
