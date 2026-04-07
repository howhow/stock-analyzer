import pytest

"""
分析 API 测试
"""

from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient


def test_analyze_stock(client: TestClient):
    """测试单次分析接口"""
    # Mock外部依赖
    with (
        patch("app.data.tushare_client.TushareClient") as mock_ts,
        patch("app.data.akshare_client.AKShareClient") as mock_ak,
    ):
        # Mock返回值
        mock_ts_instance = Mock()
        mock_ts_instance.get_stock_info = AsyncMock(return_value=None)
        mock_ts.return_value = mock_ts_instance

        mock_ak_instance = Mock()
        mock_ak_instance.get_stock_info = AsyncMock(return_value=None)
        mock_ak.return_value = mock_ak_instance

        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "stock_code": "600519.SH",
                "analysis_type": "long",
                "mode": "algorithm",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert "stock_code" in data
        assert "total_score" in data


def test_analyze_stock_invalid_code(client: TestClient):
    """测试无效股票代码 - 目前返回 mock 数据"""
    with (
        patch("app.data.tushare_client.TushareClient") as mock_ts,
        patch("app.data.akshare_client.AKShareClient") as mock_ak,
    ):
        mock_ts_instance = Mock()
        mock_ts_instance.get_stock_info = AsyncMock(return_value=None)
        mock_ts.return_value = mock_ts_instance

        mock_ak_instance = Mock()
        mock_ak_instance.get_stock_info = AsyncMock(return_value=None)
        mock_ak.return_value = mock_ak_instance

        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "stock_code": "INVALID",
                "analysis_type": "long",
            },
        )
        # Mock 阶段暂时返回 200
        assert response.status_code == 200


def test_batch_analyze(client: TestClient):
    """测试批量分析接口"""
    with (
        patch("app.data.tushare_client.TushareClient") as mock_ts,
        patch("app.data.akshare_client.AKShareClient") as mock_ak,
    ):
        mock_ts_instance = Mock()
        mock_ts_instance.get_stock_info = AsyncMock(return_value=None)
        mock_ts.return_value = mock_ts_instance

        mock_ak_instance = Mock()
        mock_ak_instance.get_stock_info = AsyncMock(return_value=None)
        mock_ak.return_value = mock_ak_instance

        response = client.post(
            "/api/v1/analysis/batch-analyze",
            json={
                "stock_codes": ["600519.SH", "000001.SZ"],
                "analysis_type": "both",
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"


def test_get_analysis_result_not_found(client: TestClient):
    """测试获取不存在的分析结果"""
    response = client.get("/api/v1/analysis/result/nonexistent-id")
    assert response.status_code == 404
