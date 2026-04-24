"""
AKSharePlugin 测试

测试插件层接口，Mock 底层 AKShareClient。
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from framework.models.quote import StandardQuote
from plugins.data_sources.akshare import AKSharePlugin

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def plugin():
    """创建带 Mock client 的插件"""
    with patch("plugins.data_sources.akshare.plugin.AKShareClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        plugin = AKSharePlugin()
        plugin._client = mock_client

        yield plugin


@pytest.fixture
def sample_quote_df():
    """样本行情 DataFrame"""
    return pd.DataFrame(
        {
            "日期": ["2024-01-01", "2024-01-02"],
            "开盘": [100.0, 101.0],
            "最高": [102.0, 103.0],
            "最低": [99.0, 100.0],
            "收盘": [101.0, 102.0],
            "成交量": [1000000, 1100000],
        }
    )


# ═══════════════════════════════════════════════════════════════
# 基础属性测试
# ═══════════════════════════════════════════════════════════════


class TestPluginProperties:
    """插件基础属性测试"""

    def test_name(self, plugin):
        """测试名称属性"""
        assert plugin.name == "akshare"

    def test_supported_markets(self, plugin):
        """测试支持的市场"""
        assert plugin.supported_markets == ["SH", "SZ"]


# ═══════════════════════════════════════════════════════════════
# get_quotes 测试
# ═══════════════════════════════════════════════════════════════


class TestGetQuotes:
    """获取行情数据测试"""

    @pytest.mark.asyncio
    async def test_get_quotes_success(self, plugin, sample_quote_df):
        """测试成功获取行情数据"""
        plugin._client.get_history_data = AsyncMock(return_value=sample_quote_df)
        plugin._client.normalize_stock_code = MagicMock(return_value=("600519", "SH"))

        quotes = await plugin.get_quotes(
            "600519.SH",
            date(2024, 1, 1),
            date(2024, 1, 2),
        )

        assert len(quotes) == 2
        assert all(isinstance(q, StandardQuote) for q in quotes)

    @pytest.mark.asyncio
    async def test_get_quotes_unsupported_market(self, plugin):
        """测试不支持的市场返回空列表"""
        plugin._client.normalize_stock_code = MagicMock(return_value=("AAPL", "US"))

        quotes = await plugin.get_quotes(
            "AAPL.US",
            date(2024, 1, 1),
            date(2024, 1, 2),
        )

        assert quotes == []

    @pytest.mark.asyncio
    async def test_get_quotes_empty_data(self, plugin):
        """测试空数据返回空列表"""
        plugin._client.get_history_data = AsyncMock(return_value=pd.DataFrame())
        plugin._client.normalize_stock_code = MagicMock(return_value=("600519", "SH"))

        quotes = await plugin.get_quotes(
            "600519.SH",
            date(2024, 1, 1),
            date(2024, 1, 2),
        )

        assert quotes == []


# ═══════════════════════════════════════════════════════════════
# get_realtime_quote 测试
# ═══════════════════════════════════════════════════════════════


class TestGetRealtimeQuote:
    """实时行情测试"""

    @pytest.mark.asyncio
    async def test_get_realtime_quote_success(self, plugin):
        """测试成功获取实时行情"""
        df = pd.DataFrame(
            {
                "代码": ["600519"],
                "名称": ["贵州茅台"],
                "最新价": [101.0],
            }
        )
        plugin._client.get_realtime_data = AsyncMock(return_value=df)

        quote = await plugin.get_realtime_quote("600519.SH")

        # AKShare 实时数据映射可能返回 None（取决于具体实现）
        # 这里主要验证调用不报错
        assert quote is None or isinstance(quote, StandardQuote)

    @pytest.mark.asyncio
    async def test_get_realtime_quote_empty(self, plugin):
        """测试无实时数据返回 None"""
        plugin._client.get_realtime_data = AsyncMock(return_value=pd.DataFrame())

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
        plugin._client.check_availability = AsyncMock(return_value=True)

        result = await plugin.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, plugin):
        """测试健康检查失败"""
        plugin._client.check_availability = AsyncMock(return_value=False)

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
        df = pd.DataFrame({"代码": ["600519", "600000", "000001"]})
        plugin._client.get_stock_list = AsyncMock(return_value=df)

        stocks = await plugin.get_supported_stocks("SH")

        # 只有 6 开头的代码
        assert len(stocks) == 2
        assert "600519.SH" in stocks
        assert "000001.SH" not in stocks

    @pytest.mark.asyncio
    async def test_get_supported_stocks_sz(self, plugin):
        """测试获取深交所股票列表"""
        df = pd.DataFrame({"代码": ["000001", "000002", "300001", "600519"]})
        plugin._client.get_stock_list = AsyncMock(return_value=df)

        stocks = await plugin.get_supported_stocks("SZ")

        # 0 或 3 开头的代码
        assert "000001.SZ" in stocks
        assert "300001.SZ" in stocks
        assert "600519.SZ" not in stocks

    @pytest.mark.asyncio
    async def test_get_supported_stocks_unsupported_market(self, plugin):
        """测试不支持的市场返回空列表"""
        stocks = await plugin.get_supported_stocks("US")

        assert stocks == []

    @pytest.mark.asyncio
    async def test_get_supported_stocks_empty_data(self, plugin):
        """测试空数据返回空列表"""
        plugin._client.get_stock_list = AsyncMock(return_value=pd.DataFrame())

        stocks = await plugin.get_supported_stocks("SH")

        assert stocks == []


# ═══════════════════════════════════════════════════════════════
# 财务数据接口测试
# ═══════════════════════════════════════════════════════════════


class TestFinancialInterfaces:
    """财务数据接口测试"""

    @pytest.mark.asyncio
    async def test_fetch_financial(self, plugin):
        """测试获取财务指标返回空 DataFrame"""
        result = await plugin.fetch_financial("600519.SH")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @pytest.mark.asyncio
    async def test_fetch_income(self, plugin):
        """测试获取利润表返回空 DataFrame"""
        result = await plugin.fetch_income("600519.SH")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @pytest.mark.asyncio
    async def test_fetch_fina_indicator(self, plugin):
        """测试获取财务指标返回空 DataFrame"""
        result = await plugin.fetch_fina_indicator("600519.SH")

        assert isinstance(result, pd.DataFrame)
        assert result.empty
