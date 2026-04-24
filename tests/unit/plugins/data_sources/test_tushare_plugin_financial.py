"""Test TusharePlugin financial data interfaces"""

from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from plugins.data_sources.tushare.plugin import TusharePlugin


class TestTusharePluginFinancial:
    """TusharePlugin 财务数据接口测试"""

    @pytest.fixture
    def plugin(self):
        """创建 Plugin 实例（Mock 客户端）"""
        with patch.object(TusharePlugin, "__init__", lambda self, **kwargs: None):
            plugin = TusharePlugin()
            plugin.name = "tushare"
            plugin.supported_markets = ["SH", "SZ"]
            plugin._client = MagicMock()
            return plugin

    @pytest.mark.asyncio
    async def test_fetch_financial_success(self, plugin):
        """fetch_financial: 成功获取每日财务指标"""
        mock_df = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "trade_date": ["20240101"],
                "pe": [30.5],
                "pb": [8.2],
                "turnover_rate": [1.5],
            }
        )
        plugin._client.get_daily_basic = AsyncMock(return_value=mock_df)

        df = await plugin.fetch_financial("600519.SH")

        assert df is not None
        assert len(df) == 1
        assert df["pe"].iloc[0] == 30.5
        assert df["pb"].iloc[0] == 8.2
        plugin._client.get_daily_basic.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_financial_no_data(self, plugin):
        """fetch_financial: 无数据时抛出异常"""
        from plugins.data_sources.tushare.exceptions import TushareNoDataError

        plugin._client.get_daily_basic = AsyncMock(return_value=pd.DataFrame())

        with pytest.raises(TushareNoDataError):
            await plugin.fetch_financial("600519.SH")

    @pytest.mark.asyncio
    async def test_fetch_income_success(self, plugin):
        """fetch_income: 成功获取利润表数据"""
        mock_df = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "ann_date": ["20240331"],
                "total_revenue": [1500000000.0],
                "n_income": [500000000.0],
            }
        )
        plugin._client.get_income = AsyncMock(return_value=mock_df)

        df = await plugin.fetch_income("600519.SH")

        assert df is not None
        assert len(df) == 1
        assert df["total_revenue"].iloc[0] == 1500000000.0
        assert df["n_income"].iloc[0] == 500000000.0
        plugin._client.get_income.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_income_no_data(self, plugin):
        """fetch_income: 无数据时抛出异常"""
        from plugins.data_sources.tushare.exceptions import TushareNoDataError

        plugin._client.get_income = AsyncMock(return_value=pd.DataFrame())

        with pytest.raises(TushareNoDataError):
            await plugin.fetch_income("600519.SH")

    @pytest.mark.asyncio
    async def test_fetch_fina_indicator_success(self, plugin):
        """fetch_fina_indicator: 成功获取财务指标数据"""
        mock_df = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "ann_date": ["20240331"],
                "roe": [15.5],
                "roe_diluted": [14.8],
            }
        )
        plugin._client.get_fina_indicator = AsyncMock(return_value=mock_df)

        df = await plugin.fetch_fina_indicator("600519.SH")

        assert df is not None
        assert len(df) == 1
        assert df["roe"].iloc[0] == 15.5
        plugin._client.get_fina_indicator.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_fina_indicator_no_data(self, plugin):
        """fetch_fina_indicator: 无数据时抛出异常"""
        from plugins.data_sources.tushare.exceptions import TushareNoDataError

        plugin._client.get_fina_indicator = AsyncMock(return_value=pd.DataFrame())

        with pytest.raises(TushareNoDataError):
            await plugin.fetch_fina_indicator("600519.SH")

    @pytest.mark.asyncio
    async def test_fetch_financial_normalizes_code(self, plugin):
        """fetch_financial: 自动标准化股票代码"""
        mock_df = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "pe": [30.5],
            }
        )
        plugin._client.get_daily_basic = AsyncMock(return_value=mock_df)

        # 传入不带后缀的代码
        df = await plugin.fetch_financial("600519")

        assert df is not None
        # 验证客户端被调用时使用了标准化后的代码
        call_args = plugin._client.get_daily_basic.call_args
        assert call_args[1]["ts_code"] == "600519.SH"

    @pytest.mark.asyncio
    async def test_fetch_financial_api_error(self, plugin):
        """fetch_financial: API 错误时抛出异常"""
        from plugins.data_sources.tushare.exceptions import TushareError

        plugin._client.get_daily_basic = AsyncMock(side_effect=TushareError("API 错误"))

        with pytest.raises(TushareError):
            await plugin.fetch_financial("600519.SH")
