"""
Pytest 配置
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

# ============================================================
# 国际化策略 - 统一使用中文
# ============================================================

RECOMMENDATIONS_ZH = ["强烈买入", "买入", "持有", "减持", "卖出"]


def assert_valid_recommendation(recommendation: str):
    """验证建议值是否有效"""
    assert recommendation in RECOMMENDATIONS_ZH, f"无效的建议值: {recommendation}"


# ============================================================
# Fixtures
# ============================================================


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
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ============================================================
# Mock 外部依赖 - 自动应用于所有测试
# ============================================================


@pytest.fixture(autouse=True)
def mock_external_apis():
    """自动Mock所有外部API调用"""
    from datetime import date, timedelta

    from app.models.stock import DailyQuote, StockInfo

    # 创建mock数据
    mock_stock_info = StockInfo(
        code="600519.SH",
        name="贵州茅台",
        market="SH",
        industry="白酒",
        list_date=None,
    )

    mock_quotes = [
        DailyQuote(
            stock_code="600519.SH",
            trade_date=date.today() - timedelta(days=i),
            open=1800.0,
            close=1810.0,
            high=1820.0,
            low=1790.0,
            volume=1000000.0,
            amount=1800000000.0,
        )
        for i in range(10)
    ]

    with (
        patch("app.data.tushare_client.TushareClient") as mock_ts,
        patch("app.data.akshare_client.AKShareClient") as mock_ak,
    ):
        # Mock Tushare
        ts_instance = Mock()
        ts_instance.get_stock_info = AsyncMock(return_value=mock_stock_info)
        ts_instance.get_daily_quotes = AsyncMock(return_value=mock_quotes)
        mock_ts.return_value = ts_instance

        # Mock AKShare
        ak_instance = Mock()
        ak_instance.get_stock_info = AsyncMock(return_value=mock_stock_info)
        ak_instance.get_daily_quotes = AsyncMock(return_value=mock_quotes)
        mock_ak.return_value = ak_instance

        yield


# ============================================================
# 可选的手动Mock fixtures
# ============================================================


@pytest.fixture
def mock_tushare():
    """Mock Tushare 客户端"""
    from app.models.stock import StockInfo

    with patch("app.data.tushare_client.TushareClient") as mock:
        instance = Mock()
        instance.get_stock_info = AsyncMock(
            return_value=StockInfo(
                code="600519.SH",
                name="贵州茅台",
                market="SH",
                industry="白酒",
                list_date=None,
            )
        )
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_akshare():
    """Mock AKShare 客户端"""
    from app.models.stock import StockInfo

    with patch("app.data.akshare_client.AKShareClient") as mock:
        instance = Mock()
        instance.get_stock_info = AsyncMock(
            return_value=StockInfo(
                code="600519.SH",
                name="贵州茅台",
                market="SH",
                industry="白酒",
                list_date=None,
            )
        )
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_data_fetcher(mock_tushare, mock_akshare):
    """Mock DataFetcher"""
    from app.data.data_fetcher import DataFetcher

    with patch("app.data.data_fetcher.DataFetcher") as mock:
        instance = Mock(spec=DataFetcher)
        instance.get_stock_info = AsyncMock(
            return_value=StockInfo(
                code="600519.SH",
                name="贵州茅台",
                market="SH",
                industry="白酒",
                list_date=None,
            )
        )
        mock.return_value = instance
        yield instance
