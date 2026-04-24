"""Web服务启动验证集成测试"""

import pytest
import requests


@pytest.mark.integration
class TestServiceStartup:
    """全服务启动验证"""

    def test_api_service_running(self, api_service):
        """验证API服务已启动"""
        port = api_service["port"]
        response = requests.get(f"http://localhost:{port}/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok" or data.get("status") == "healthy"

    def test_api_analysis_endpoint(self, api_service):
        """验证API分析端点可用"""
        port = api_service["port"]
        response = requests.get(
            f"http://localhost:{port}/api/v1/analysis/688981.SH",
            timeout=120,
        )
        # 可能返回200或202（异步任务）
        assert response.status_code in [200, 202]
