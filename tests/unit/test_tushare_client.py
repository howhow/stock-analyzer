"""
Tushare 客户端测试

测试 app/data/tushare_client.py 中的 TushareClient 类。
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from app.data.base import DataSourceError
from app.data.tushare_client import TushareClient


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_tushare_pro():
    """创建模拟 Tushare Pro API"""
    pro = MagicMock()

    # 模拟股票基本信息
    pro.stock_basic.return_value = pd.DataFrame(
        {
            "ts_code": ["600519.SH"],
            "name": ["贵州茅台"],
            "industry": ["白酒"],
            "list_date": ["20010827"],
            "market": ["主板"],
        }
    )

    # 模拟日线行情
    pro.daily.return_value = pd.DataFrame(
        {
            "ts_code": ["600519.SH"],
            "trade_date": ["20240101"],
            "open": [1700.0],
            "high": [1750.0],
            "low": [1680.0],
            "close": [1720.0],
            "vol": [10000.0],
            "amount": [17200000.0],
        }
    )

    # 模拟财务数据
    pro.daily_basic.return_value = pd.DataFrame(
        {
            "ts_code": ["600519.SH"],
            "trade_date": ["20240101"],
            "pe": [30.0],
            "pb": [8.0],
            "turnover_rate": [0.5],
        }
    )

    # 模拟交易日历
    pro.trade_cal.return_value = pd.DataFrame(
        {
            "exchange": ["SSE"],
            "cal_date": ["20240101"],
            "is_open": [1],
        }
    )

    return pro


@pytest.fixture
def client(mock_tushare_pro):
    """创建 TushareClient 实例"""
    with patch("app.data.tushare_client.ts") as mock_ts:
        mock_ts.pro_api.return_value = mock_tushare_pro
        client = TushareClient(token="test_token")
        client.pro = mock_tushare_pro
        return client


# ============================================================
# 初始化
# ============================================================


class TestInit:
    """测试初始化"""

    def test_init_with_token(self):
        """测试带 token 初始化"""
        with patch("app.data.tushare_client.ts") as mock_ts:
            mock_ts.pro_api.return_value = MagicMock()
            client = TushareClient(token="test_token")
            assert client.token == "test_token"
            assert client.name == "tushare"

    def test_init_without_token(self):
        """测试无 token 初始化"""
        with patch("app.data.tushare_client.settings") as mock_settings:
            mock_settings.tushare_token = ""
            client = TushareClient(token="")
            assert client.pro is None


# ============================================================
# get_stock_info
# ============================================================


class TestGetStockInfo:
    """测试获取股票信息"""

    @pytest.mark.asyncio
    async def test_get_stock_info_success(self, client):
        """测试正常获取"""
        result = await client.get_stock_info("600519.SH")
        assert result.code == "600519.SH"
        assert result.name == "贵州茅台"

    @pytest.mark.asyncio
    async def test_get_stock_info_no_token(self):
        """测试无 token"""
        with patch("app.data.tushare_client.ts") as mock_ts:
            mock_ts.pro_api.return_value = None
            client = TushareClient(token="")
            client.pro = None
            with pytest.raises(DataSourceError):
                await client.get_stock_info("600519.SH")


# ============================================================
# get_daily_quotes
# ============================================================


class TestGetDailyQuotes:
    """测试获取日线行情"""

    @pytest.mark.asyncio
    async def test_get_daily_quotes_success(self, client):
        """测试正常获取"""
        result = await client.get_daily_quotes(
            "600519.SH",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_daily_quotes_empty(self, client):
        """测试空数据"""
        client.pro.daily.return_value = pd.DataFrame()
        result = await client.get_daily_quotes(
            "600519.SH",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert result == []


# ============================================================
# get_intraday_quotes
# ============================================================


class TestGetIntradayQuotes:
    """测试获取分钟线"""

    @pytest.mark.asyncio
    async def test_get_intraday_quotes(self, client):
        """测试分钟线（免费版不支持）"""
        result = await client.get_intraday_quotes("600519.SH")
        assert result == []


# ============================================================
# get_financial_data
# ============================================================


class TestGetFinancialData:
    """测试获取财务数据"""

    @pytest.mark.asyncio
    async def test_get_financial_data_success(self, client):
        """测试正常获取"""
        result = await client.get_financial_data("600519.SH")
        assert result is not None
        assert result.stock_code == "600519.SH"

    @pytest.mark.asyncio
    async def test_get_financial_data_empty(self, client):
        """测试空数据"""
        client.pro.daily_basic.return_value = pd.DataFrame()
        result = await client.get_financial_data("600519.SH")
        assert result is None


# ============================================================
# health_check
# ============================================================


class TestHealthCheck:
    """测试健康检查"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """测试健康检查通过"""
        result = await client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """测试健康检查失败"""
        client.pro.trade_cal.side_effect = Exception("API Error")
        result = await client.health_check()
        assert result is False


# ============================================================
# _parse_date
# ============================================================


class TestParseDate:
    """测试日期解析"""

    def test_parse_date_yyyymmdd(self, client):
        """测试 YYYYMMDD 格式"""
        result = client._parse_date("20240101")
        assert result == date(2024, 1, 1)

    def test_parse_date_iso(self, client):
        """测试 ISO 格式"""
        result = client._parse_date("2024-01-01")
        assert result == date(2024, 1, 1)

    def test_parse_date_none(self, client):
        """测试 None"""
        result = client._parse_date(None)
        assert result is None

    def test_parse_date_invalid(self, client):
        """测试无效格式"""
        result = client._parse_date("invalid")
        assert result is None


# ============================================================
# close
# ============================================================


class TestClose:
    """测试关闭客户端"""

    @pytest.mark.asyncio
    async def test_close(self, client):
        """测试关闭"""
        client._http_client = MagicMock()
        client._http_client.aclose = AsyncMock()
        await client.close()
        assert client._http_client is None
