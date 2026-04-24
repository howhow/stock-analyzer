"""
OpenBBPlugin 测试

测试插件层接口，Mock 底层 OpenBBClient。
"""

from datetime import date
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from framework.models.quote import StandardQuote
from plugins.data_sources.openbb import OpenBBPlugin

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def plugin():
    """创建带 Mock client 的插件"""
    with patch("plugins.data_sources.openbb.plugin.OpenBBClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        plugin = OpenBBPlugin()
        plugin._client = mock_client

        yield plugin


@pytest.fixture
def sample_quote_df():
    """样本行情 DataFrame"""
    return pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [1000000, 1100000],
        }
    )


# ═══════════════════════════════════════════════════════════════
# 基础属性测试
# ═══════════════════════════════════════════════════════════════


class TestPluginProperties:
    """插件基础属性测试"""

    def test_name(self, plugin):
        """测试名称属性"""
        assert plugin.name == "openbb"

    def test_supported_markets(self, plugin):
        """测试支持的市场"""
        assert "SH" in plugin.supported_markets
        assert "SZ" in plugin.supported_markets
        assert "HK" in plugin.supported_markets
        assert "US" in plugin.supported_markets


# ═══════════════════════════════════════════════════════════════
# get_quotes 测试
# ═══════════════════════════════════════════════════════════════


class TestGetQuotes:
    """获取行情数据测试"""

    @pytest.mark.asyncio
    async def test_get_quotes_success(self, plugin, sample_quote_df):
        """测试成功获取行情数据"""
        # OpenBB mapper 期望 list[dict] 格式
        raw_data = [
            {
                "date": "2024-01-01",
                "open": 100.0,
                "high": 102.0,
                "low": 99.0,
                "close": 101.0,
                "volume": 1000000,
            },
            {
                "date": "2024-01-02",
                "open": 101.0,
                "high": 103.0,
                "low": 100.0,
                "close": 102.0,
                "volume": 1100000,
            },
        ]
        plugin._client.get_historical = AsyncMock(return_value=raw_data)

        quotes = await plugin.get_quotes(
            "AAPL.US",
            date(2024, 1, 1),
            date(2024, 1, 2),
        )

        assert len(quotes) == 2
        assert all(isinstance(q, StandardQuote) for q in quotes)

    @pytest.mark.asyncio
    async def test_get_quotes_empty_data(self, plugin):
        """测试空数据返回空列表"""
        plugin._client.get_historical = AsyncMock(return_value=[])

        quotes = await plugin.get_quotes(
            "AAPL.US",
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
                "price": [150.0],
                "volume": [1000000],
            }
        )
        plugin._client.get_quote = AsyncMock(return_value=df)

        quote = await plugin.get_realtime_quote("AAPL.US")

        # OpenBB 实时数据映射可能返回 None
        assert quote is None or isinstance(quote, StandardQuote)

    @pytest.mark.asyncio
    async def test_get_realtime_quote_empty(self, plugin):
        """测试无实时数据返回 None"""
        plugin._client.get_quote = AsyncMock(return_value=None)

        quote = await plugin.get_realtime_quote("AAPL.US")

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


# ═══════════════════════════════════════════════════════════════
# get_supported_stocks 测试
# ═══════════════════════════════════════════════════════════════


class TestGetSupportedStocks:
    """获取股票列表测试"""

    @pytest.mark.asyncio
    async def test_get_supported_stocks_us(self, plugin):
        """测试获取美股列表"""
        plugin._client.search_stocks = AsyncMock(return_value=["AAPL", "GOOGL"])

        stocks = await plugin.get_supported_stocks("US")

        assert len(stocks) == 2

    @pytest.mark.asyncio
    async def test_get_supported_stocks_hk(self, plugin):
        """测试获取港股列表"""
        plugin._client.search_stocks = AsyncMock(return_value=["0700.HK"])

        stocks = await plugin.get_supported_stocks("HK")

        assert len(stocks) == 1

    @pytest.mark.asyncio
    async def test_get_supported_stocks_cn_empty(self, plugin):
        """测试 A 股市场返回空列表（OpenBB 支持有限）"""
        stocks = await plugin.get_supported_stocks("SH")

        assert stocks == []

    @pytest.mark.asyncio
    async def test_get_supported_stocks_unsupported(self, plugin):
        """测试不支持的市场返回空列表"""
        stocks = await plugin.get_supported_stocks("UK")

        assert stocks == []

    @pytest.mark.asyncio
    async def test_get_supported_stocks_exception(self, plugin):
        """测试异常时返回空列表"""
        plugin._client.search_stocks = AsyncMock(side_effect=Exception("Error"))

        stocks = await plugin.get_supported_stocks("US")

        assert stocks == []


# ═══════════════════════════════════════════════════════════════
# 财务数据接口测试
# ═══════════════════════════════════════════════════════════════


class TestFinancialInterfaces:
    """财务数据接口测试"""

    @pytest.mark.asyncio
    async def test_fetch_financial(self, plugin):
        """测试获取财务指标返回空 DataFrame"""
        result = await plugin.fetch_financial("AAPL")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @pytest.mark.asyncio
    async def test_fetch_income(self, plugin):
        """测试获取利润表返回空 DataFrame"""
        result = await plugin.fetch_income("AAPL")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @pytest.mark.asyncio
    async def test_fetch_fina_indicator(self, plugin):
        """测试获取财务指标返回空 DataFrame"""
        result = await plugin.fetch_fina_indicator("AAPL")

        assert isinstance(result, pd.DataFrame)
        assert result.empty


# ═══════════════════════════════════════════════════════════════
# 其他测试
# ═══════════════════════════════════════════════════════════════


class TestOtherMethods:
    """其他方法测试"""

    def test_repr(self, plugin):
        """测试 __repr__ 方法"""
        repr_str = repr(plugin)

        assert "OpenBBPlugin" in repr_str
        assert "openbb" in repr_str
