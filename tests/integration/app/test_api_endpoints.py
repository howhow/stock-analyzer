"""API 端点集成测试 — 端到端验证"""

import pytest


@pytest.mark.integration
class TestAPIEndpointsIntegration:
    """API 端点端到端集成测试"""

    def test_api_health_check(self):
        """验证 API 健康检查端点"""
        import requests

        try:
            # 假设 API 运行在本地
            response = requests.get("http://localhost:8000/api/v1/health", timeout=2)

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "ok"
        except requests.exceptions.ConnectionError:
            pytest.skip("API 服务未运行")
        except requests.exceptions.Timeout:
            pytest.skip("API 服务响应超时")
