"""
LocalPlugin 测试

测试本地数据源插件接口。
"""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from framework.models.quote import StandardQuote
from plugins.data_sources.local import LocalPlugin, LocalPluginConfig

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def sample_df():
    """样本数据"""
    return pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "open": [100.0, 101.0, 102.0],
            "high": [102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0],
            "close": [101.0, 102.0, 103.0],
            "volume": [1000000, 1100000, 1200000],
        }
    )


# ═══════════════════════════════════════════════════════════════
# 基础属性测试
# ═══════════════════════════════════════════════════════════════


class TestPluginProperties:
    """插件基础属性测试"""

    def test_name(self):
        """测试名称属性"""
        plugin = LocalPlugin()
        assert plugin.name == "local"

    def test_supported_markets(self):
        """测试支持的市场"""
        plugin = LocalPlugin()
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
    async def test_get_quotes_success(self, sample_df):
        """测试成功获取行情数据"""
        plugin = LocalPlugin()

        with patch.object(
            plugin._loader, "load_with_date_filter", return_value=sample_df
        ):
            quotes = await plugin.get_quotes(
                "600519.SH",
                date(2024, 1, 1),
                date(2024, 1, 3),
            )

        assert len(quotes) == 3
        assert all(isinstance(q, StandardQuote) for q in quotes)
        assert quotes[0].close == 101.0

    @pytest.mark.asyncio
    async def test_get_quotes_empty_data(self):
        """测试空数据抛出异常"""
        plugin = LocalPlugin()

        with patch.object(
            plugin._loader, "load_with_date_filter", return_value=pd.DataFrame()
        ):
            with pytest.raises(Exception):  # NoDataError
                await plugin.get_quotes(
                    "600519.SH",
                    date(2024, 1, 1),
                    date(2024, 1, 3),
                )


# ═══════════════════════════════════════════════════════════════
# get_realtime_quote 测试
# ═══════════════════════════════════════════════════════════════


class TestGetRealtimeQuote:
    """实时行情测试"""

    @pytest.mark.asyncio
    async def test_get_realtime_quote_returns_none(self):
        """测试实时行情始终返回 None"""
        plugin = LocalPlugin()

        quote = await plugin.get_realtime_quote("600519.SH")

        assert quote is None


# ═══════════════════════════════════════════════════════════════
# health_check 测试
# ═══════════════════════════════════════════════════════════════


class TestHealthCheck:
    """健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check_existing_dir(self, tmp_path):
        """测试目录存在时返回 True"""
        config = LocalPluginConfig(data_dir=str(tmp_path))
        plugin = LocalPlugin(config=config)

        result = await plugin.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_nonexistent_dir(self):
        """测试目录不存在时返回 False"""
        config = LocalPluginConfig(data_dir="/nonexistent/path")
        plugin = LocalPlugin(config=config)

        result = await plugin.health_check()

        assert result is False


# ═══════════════════════════════════════════════════════════════
# get_supported_stocks 测试
# ═══════════════════════════════════════════════════════════════


class TestGetSupportedStocks:
    """获取股票列表测试"""

    @pytest.mark.asyncio
    async def test_get_supported_stocks_all(self):
        """测试获取所有股票"""
        plugin = LocalPlugin()

        with patch.object(
            plugin._loader,
            "list_available_stocks",
            return_value=["600519.SH", "000001.SZ"],
        ):
            stocks = await plugin.get_supported_stocks("all")

        assert len(stocks) == 2

    @pytest.mark.asyncio
    async def test_get_supported_stocks_sh(self):
        """测试过滤上交所股票"""
        plugin = LocalPlugin()

        with patch.object(
            plugin._loader,
            "list_available_stocks",
            return_value=["600519.SH", "000001.SZ", "AAPL.US"],
        ):
            stocks = await plugin.get_supported_stocks("SH")

        assert len(stocks) == 1
        assert "600519.SH" in stocks

    @pytest.mark.asyncio
    async def test_get_supported_stocks_us(self):
        """测试过滤美股"""
        plugin = LocalPlugin()

        with patch.object(
            plugin._loader,
            "list_available_stocks",
            return_value=["600519.SH", "AAPL.US"],
        ):
            stocks = await plugin.get_supported_stocks("US")

        assert len(stocks) == 1
        assert "AAPL.US" in stocks


# ═══════════════════════════════════════════════════════════════
# 财务数据接口测试
# ═══════════════════════════════════════════════════════════════


class TestFinancialInterfaces:
    """财务数据接口测试"""

    @pytest.mark.asyncio
    async def test_fetch_financial(self):
        """测试获取财务指标返回空 DataFrame"""
        plugin = LocalPlugin()
        result = await plugin.fetch_financial("600519.SH")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @pytest.mark.asyncio
    async def test_fetch_income(self):
        """测试获取利润表返回空 DataFrame"""
        plugin = LocalPlugin()
        result = await plugin.fetch_income("600519.SH")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @pytest.mark.asyncio
    async def test_fetch_fina_indicator(self):
        """测试获取财务指标返回空 DataFrame"""
        plugin = LocalPlugin()
        result = await plugin.fetch_fina_indicator("600519.SH")

        assert isinstance(result, pd.DataFrame)
        assert result.empty


# ═══════════════════════════════════════════════════════════════
# 工具方法测试
# ═══════════════════════════════════════════════════════════════


class TestUtilityMethods:
    """工具方法测试"""

    def test_infer_currency_us(self):
        """测试推断美元"""
        plugin = LocalPlugin()
        assert plugin._infer_currency("AAPL.US") == "USD"

    def test_infer_currency_hk(self):
        """测试推断港币"""
        plugin = LocalPlugin()
        assert plugin._infer_currency("0700.HK") == "HKD"

    def test_infer_currency_cn(self):
        """测试推断人民币"""
        plugin = LocalPlugin()
        assert plugin._infer_currency("600519.SH") == "CNY"
        assert plugin._infer_currency("000001.SZ") == "CNY"
