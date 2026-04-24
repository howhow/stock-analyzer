"""
TusharePlugin 测试

测试插件层接口，Mock 底层 TushareClient。
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from framework.models.quote import StandardQuote
from plugins.data_sources.tushare import TusharePlugin
from plugins.data_sources.tushare.exceptions import TushareError, TushareNoDataError

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def plugin():
    """创建带 Mock client 的插件"""
    with patch("plugins.data_sources.tushare.plugin.TushareClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        plugin = TusharePlugin(token="test_token")
        plugin._client = mock_client

        yield plugin


@pytest.fixture
def sample_quote_df():
    """样本行情 DataFrame"""
    return pd.DataFrame(
        {
            "ts_code": ["600519.SH", "600519.SH"],
            "trade_date": ["20240101", "20240102"],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "vol": [1000000, 1100000],
        }
    )


# ═══════════════════════════════════════════════════════════════
# 基础属性测试
# ═══════════════════════════════════════════════════════════════


class TestPluginProperties:
    """插件基础属性测试"""

    def test_name(self, plugin):
        """测试名称属性"""
        assert plugin.name == "tushare"

    def test_supported_markets(self, plugin):
        """测试支持的市场"""
        assert plugin.supported_markets == ["SH", "SZ"]

    def test_supported_currencies(self, plugin):
        """测试支持的货币"""
        assert plugin.supported_currencies == ["CNY"]


# ═══════════════════════════════════════════════════════════════
# get_quotes 测试
# ═══════════════════════════════════════════════════════════════


class TestGetQuotes:
    """获取行情数据测试"""

    @pytest.mark.asyncio
    async def test_get_quotes_success(self, plugin, sample_quote_df):
        """测试成功获取行情数据"""
        plugin._client.get_daily_quotes = AsyncMock(return_value=sample_quote_df)

        quotes = await plugin.get_quotes(
            "600519.SH",
            date(2024, 1, 1),
            date(2024, 1, 2),
        )

        assert len(quotes) == 2
        assert all(isinstance(q, StandardQuote) for q in quotes)
        plugin._client.get_daily_quotes.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_quotes_empty_data(self, plugin):
        """测试空数据返回"""
        plugin._client.get_daily_quotes = AsyncMock(return_value=pd.DataFrame())

        with pytest.raises(TushareNoDataError):
            await plugin.get_quotes(
                "600519.SH",
                date(2024, 1, 1),
                date(2024, 1, 2),
            )

    @pytest.mark.asyncio
    async def test_get_quotes_client_error(self, plugin):
        """测试客户端错误"""
        plugin._client.get_daily_quotes = AsyncMock(
            side_effect=TushareError("API Error", code="1000")
        )

        with pytest.raises(TushareError):
            await plugin.get_quotes(
                "600519.SH",
                date(2024, 1, 1),
                date(2024, 1, 2),
            )

    @pytest.mark.asyncio
    async def test_get_quotes_code_normalization(self, plugin, sample_quote_df):
        """测试股票代码标准化"""
        plugin._client.get_daily_quotes = AsyncMock(return_value=sample_quote_df)

        # 传入不带后缀的代码
        await plugin.get_quotes(
            "600519",
            date(2024, 1, 1),
            date(2024, 1, 2),
        )

        # 验证标准化后的代码被传递给 client
        call_args = plugin._client.get_daily_quotes.call_args
        assert call_args.kwargs["ts_code"] == "600519.SH"


# ═══════════════════════════════════════════════════════════════
# get_realtime_quote 测试
# ═══════════════════════════════════════════════════════════════


class TestGetRealtimeQuote:
    """实时行情测试"""

    @pytest.mark.asyncio
    async def test_get_realtime_quote_success(self, plugin, sample_quote_df):
        """测试成功获取实时行情"""
        plugin._client.get_realtime_quote = AsyncMock(return_value=sample_quote_df)

        quote = await plugin.get_realtime_quote("600519.SH")

        assert isinstance(quote, StandardQuote)
        assert quote.close == 101.0

    @pytest.mark.asyncio
    async def test_get_realtime_quote_empty(self, plugin):
        """测试无实时数据返回 None"""
        plugin._client.get_realtime_quote = AsyncMock(return_value=pd.DataFrame())

        quote = await plugin.get_realtime_quote("600519.SH")

        assert quote is None

    @pytest.mark.asyncio
    async def test_get_realtime_quote_exception(self, plugin):
        """测试异常时返回 None"""
        plugin._client.get_realtime_quote = AsyncMock(side_effect=Exception("Timeout"))

        quote = await plugin.get_realtime_quote("600519.SH")

        assert quote is None


# ═══════════════════════════════════════════════════════════════
# health_check 测试
# ═══════════════════════════════════════════════════════════════


class TestHealthCheck:
    """健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, plugin):
        """测试健康检查通过"""
        plugin._client.health_check = AsyncMock(return_value=True)

        result = await plugin.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, plugin):
        """测试健康检查失败"""
        plugin._client.health_check = AsyncMock(return_value=False)

        result = await plugin.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, plugin):
        """测试健康检查异常"""
        plugin._client.health_check = AsyncMock(side_effect=Exception("Error"))

        result = await plugin.health_check()

        assert result is False


# ═══════════════════════════════════════════════════════════════
# get_supported_stocks 测试
# ═══════════════════════════════════════════════════════════════


class TestGetSupportedStocks:
    """获取股票列表测试"""

    @pytest.mark.asyncio
    async def test_get_supported_stocks_sh(self, plugin):
        """测试获取上交所股票列表"""
        df = pd.DataFrame({"ts_code": ["600519.SH", "600000.SH"]})
        plugin._client.get_stock_basic = AsyncMock(return_value=df)

        stocks = await plugin.get_supported_stocks("SH")

        assert len(stocks) == 2
        assert "600519.SH" in stocks
        plugin._client.get_stock_basic.assert_called_once_with(exchange="SSE")

    @pytest.mark.asyncio
    async def test_get_supported_stocks_sz(self, plugin):
        """测试获取深交所股票列表"""
        df = pd.DataFrame({"ts_code": ["000001.SZ", "000002.SZ"]})
        plugin._client.get_stock_basic = AsyncMock(return_value=df)

        stocks = await plugin.get_supported_stocks("SZ")

        assert len(stocks) == 2
        plugin._client.get_stock_basic.assert_called_once_with(exchange="SZSE")

    @pytest.mark.asyncio
    async def test_get_supported_stocks_invalid_market(self, plugin):
        """测试无效市场代码"""
        with pytest.raises(ValueError, match="不支持的市场代码"):
            await plugin.get_supported_stocks("US")

    @pytest.mark.asyncio
    async def test_get_supported_stocks_no_ts_code(self, plugin):
        """测试返回数据无 ts_code 列"""
        df = pd.DataFrame({"other_col": [1, 2]})
        plugin._client.get_stock_basic = AsyncMock(return_value=df)

        stocks = await plugin.get_supported_stocks("SH")

        assert stocks == []


# ═══════════════════════════════════════════════════════════════
# 财务数据接口测试
# ═══════════════════════════════════════════════════════════════


class TestFinancialInterfaces:
    """财务数据接口测试"""

    @pytest.mark.asyncio
    async def test_fetch_financial_success(self, plugin):
        """测试获取财务指标"""
        df = pd.DataFrame({"pe": [20.5], "pb": [3.2]})
        plugin._client.get_daily_basic = AsyncMock(return_value=df)

        result = await plugin.fetch_financial("600519.SH")

        assert len(result) == 1
        assert result["pe"].iloc[0] == 20.5

    @pytest.mark.asyncio
    async def test_fetch_financial_empty(self, plugin):
        """测试空数据抛出异常"""
        plugin._client.get_daily_basic = AsyncMock(return_value=pd.DataFrame())

        with pytest.raises(TushareNoDataError):
            await plugin.fetch_financial("600519.SH")

    @pytest.mark.asyncio
    async def test_fetch_income_success(self, plugin):
        """测试获取利润表"""
        df = pd.DataFrame({"revenue": [1000000], "net_income": [200000]})
        plugin._client.get_income = AsyncMock(return_value=df)

        result = await plugin.fetch_income("600519.SH")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_fina_indicator_success(self, plugin):
        """测试获取财务指标"""
        df = pd.DataFrame({"roe": [15.5], "roa": [8.2]})
        plugin._client.get_fina_indicator = AsyncMock(return_value=df)

        result = await plugin.fetch_fina_indicator("600519.SH")

        assert len(result) == 1


# ═══════════════════════════════════════════════════════════════
# 工具方法测试
# ═══════════════════════════════════════════════════════════════


class TestUtilityMethods:
    """工具方法测试"""

    def test_normalize_stock_code_with_suffix(self, plugin):
        """测试已有后缀的代码"""
        assert plugin._normalize_stock_code("600519.sh") == "600519.SH"

    def test_normalize_stock_code_sh(self, plugin):
        """测试上交所代码推断"""
        assert plugin._normalize_stock_code("600519") == "600519.SH"
        assert plugin._normalize_stock_code("688888") == "688888.SH"

    def test_normalize_stock_code_sz(self, plugin):
        """测试深交所代码推断"""
        assert plugin._normalize_stock_code("000001") == "000001.SZ"
        assert plugin._normalize_stock_code("300001") == "300001.SZ"

    def test_normalize_stock_code_strip(self, plugin):
        """测试去除空白"""
        assert plugin._normalize_stock_code("  600519  ") == "600519.SH"

    @pytest.mark.asyncio
    async def test_close(self, plugin):
        """测试关闭插件"""
        plugin._client.close = AsyncMock()

        await plugin.close()

        plugin._client.close.assert_called_once()
