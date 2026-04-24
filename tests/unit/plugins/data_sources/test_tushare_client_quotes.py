"""TushareClient 行情方法测试

补充行情数据获取方法的测试覆盖。
"""

from unittest.mock import patch

import pandas as pd
import pytest

from plugins.data_sources.tushare.client import TushareClient
from plugins.data_sources.tushare.exceptions import TushareError, TushareNoDataError


class TestGetDailyQuotes:
    """测试 get_daily_quotes 日线行情"""

    @pytest.fixture
    def client(self):
        return TushareClient(token="test_token")

    @pytest.mark.asyncio
    async def test_success(self, client):
        """成功获取日线数据"""
        mock_df = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "trade_date": ["20240101"],
                "open": [100.0],
                "high": [105.0],
                "low": [99.0],
                "close": [103.0],
                "vol": [10000.0],
                "amount": [1030000.0],
            }
        )

        with patch.object(client, "_call_api", return_value=mock_df):
            result = await client.get_daily_quotes("600519.SH", "20240101", "20240101")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result["close"].iloc[0] == 103.0

    @pytest.mark.asyncio
    async def test_empty_response(self, client):
        """空数据响应"""
        with patch.object(client, "_call_api", return_value=pd.DataFrame()):
            with pytest.raises(TushareNoDataError):
                await client.get_daily_quotes("600519.SH", "20240101", "20240101")

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        """API 调用失败"""
        with patch.object(client, "_call_api", side_effect=TushareError("API错误")):
            with pytest.raises(TushareError):
                await client.get_daily_quotes("600519.SH", "20240101", "20240101")


class TestGetRealtimeQuote:
    """测试 get_realtime_quote 实时行情"""

    @pytest.fixture
    def client(self):
        return TushareClient(token="test_token")

    @pytest.mark.asyncio
    async def test_success(self, client):
        """成功获取实时数据"""
        mock_df = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "trade_date": ["20240101"],
                "open": [100.0],
                "high": [105.0],
                "low": [99.0],
                "close": [103.0],
                "vol": [10000.0],
            }
        )

        with patch.object(client, "_call_api", return_value=mock_df):
            result = await client.get_realtime_quote("600519.SH")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_no_data(self, client):
        """无实时数据返回 None（通过异常触发）"""
        with patch.object(client, "_call_api", side_effect=Exception("not supported")):
            result = await client.get_realtime_quote("600519.SH")

        assert result is None


class TestGetStockBasic:
    """测试 get_stock_basic 股票列表"""

    @pytest.fixture
    def client(self):
        return TushareClient(token="test_token")

    @pytest.mark.asyncio
    async def test_success(self, client):
        """成功获取股票列表"""
        mock_df = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "000001.SZ"],
                "name": ["贵州茅台", "平安银行"],
                "exchange": ["SSE", "SZSE"],
            }
        )

        with patch.object(client, "_call_api", return_value=mock_df):
            result = await client.get_stock_basic(exchange="SSE")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_response(self, client):
        """空响应"""
        with patch.object(client, "_call_api", return_value=pd.DataFrame()):
            with pytest.raises(TushareNoDataError):
                await client.get_stock_basic(exchange="SSE")


class TestHealthCheck:
    """测试 health_check"""

    @pytest.fixture
    def client(self):
        return TushareClient(token="test_token")

    @pytest.mark.asyncio
    async def test_healthy(self, client):
        """健康状态"""
        mock_df = pd.DataFrame({"exchange": ["SSE"], "cal_date": ["20240101"]})

        with patch.object(client, "_call_api", return_value=mock_df):
            result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_unhealthy(self, client):
        """不健康状态"""
        with patch.object(client, "_call_api", side_effect=Exception("连接失败")):
            result = await client.health_check()

        assert result is False
