import pytest

"""
分析 API 测试
"""

from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient
from app.models.stock import StockInfo


def test_analyze_stock(client: TestClient):
    """测试单次分析接口"""
    from app.api.deps import get_data_fetcher
    from app.main import app
    
    # Mock DataFetcher
    mock_fetcher = AsyncMock()
    mock_fetcher.get_stock_info = AsyncMock(
        return_value=StockInfo(
            code="600519.SH",
            name="贵州茅台",
            market="SH",
            industry="白酒",
        )
    )
    mock_fetcher.get_daily_quotes = AsyncMock(return_value=[])
    mock_fetcher.get_financial_data = AsyncMock(return_value=None)
    
    # Override dependency
    app.dependency_overrides[get_data_fetcher] = lambda: mock_fetcher

    try:
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
    finally:
        app.dependency_overrides.clear()


def test_analyze_stock_invalid_code(client: TestClient):
    """测试无效股票代码 - 目前返回 mock 数据"""
    from app.api.deps import get_data_fetcher
    from app.main import app
    
    mock_fetcher = AsyncMock()
    mock_fetcher.get_stock_info = AsyncMock(return_value=None)
    mock_fetcher.get_daily_quotes = AsyncMock(return_value=[])
    mock_fetcher.get_financial_data = AsyncMock(return_value=None)
    
    app.dependency_overrides[get_data_fetcher] = lambda: mock_fetcher

    try:
        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "stock_code": "INVALID",
                "analysis_type": "long",
            },
        )
        # Mock 阶段暂时返回 200
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_batch_analyze(client: TestClient):
    """测试批量分析接口"""
    from app.api.deps import get_data_fetcher
    from app.main import app
    
    mock_fetcher = AsyncMock()
    mock_fetcher.get_stock_info = AsyncMock(return_value=None)
    mock_fetcher.get_daily_quotes = AsyncMock(return_value=[])
    mock_fetcher.get_financial_data = AsyncMock(return_value=None)
    
    app.dependency_overrides[get_data_fetcher] = lambda: mock_fetcher

    try:
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
    finally:
        app.dependency_overrides.clear()


def test_get_analysis_result_not_found(client: TestClient):
    """测试获取不存在的分析结果"""
    response = client.get("/api/v1/analysis/result/nonexistent-id")
    assert response.status_code == 404
