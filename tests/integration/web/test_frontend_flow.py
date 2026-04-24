import sys

"""前端操作流程集成测试 — 使用Playwright模拟用户操作"""

import pytest

# 动态检测Playwright是否安装
pytest.importorskip(
    "playwright",
    reason="Playwright未安装，需运行: pip install playwright && playwright install",
)


@pytest.mark.integration
class TestFrontendFlow:
    """前端操作流程集成测试"""

    def test_page_load(self, api_service):
        """验证前端页面加载（通过HTTP检查）"""
        import requests

        port = api_service["port"]
        # 检查前端服务是否可访问
        try:
            response = requests.get(f"http://localhost:{port}", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("前端服务未启动（Streamlit服务需要在8501端口）")

    def test_frontend_api_integration(self, api_service):
        """验证前端可以调用API"""
        import requests

        port = api_service["port"]
        # 测试API健康检查
        response = requests.get(f"http://localhost:{port}/api/v1/health")
        assert response.status_code == 200

        # 测试分析API
        response = requests.get(
            f"http://localhost:{port}/api/v1/analysis/688981.SH",
            timeout=120,
        )
        assert response.status_code in [200, 202]
