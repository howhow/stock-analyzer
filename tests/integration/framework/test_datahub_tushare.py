"""DataHub真实Tushare调用集成测试 — 通过DataHub获取真实数据"""

import asyncio

import pytest


@pytest.mark.integration
class TestDataHubTushare:
    """DataHub→真实Tushare集成测试"""

    def test_fetch_daily_quotes_real(self):
        """通过DataHub获取真实日线数据"""
        from framework.data.hub import DataHub
        from plugins.data_sources.tushare.plugin import TusharePlugin

        tushare = TusharePlugin()
        datahub = DataHub(sources=[tushare])

        result = asyncio.run(datahub.fetch_daily("688981.SH"))

        # 验证返回真实数据
        assert result is not None
        assert len(result) > 0
        assert "close" in result.columns
        assert "volume" in result.columns

        # 验证数据合理性（不是mock数据）
        assert result["close"].iloc[-1] > 0
        assert result["volume"].iloc[-1] > 0

    def test_fetch_financial_data_real(self):
        """通过DataHub获取真实财务数据"""
        from framework.data.hub import DataHub
        from plugins.data_sources.tushare.plugin import TusharePlugin

        tushare = TusharePlugin()
        datahub = DataHub(sources=[tushare])

        result = asyncio.run(datahub.fetch_financial("688981.SH"))

        # 验证返回真实财务指标
        assert result is not None
        assert "pe" in result.columns or "pb" in result.columns or len(result) > 0

    def test_fetch_income_data_real(self):
        """通过DataHub获取真实收入数据"""
        from framework.data.hub import DataHub
        from plugins.data_sources.tushare.plugin import TusharePlugin

        tushare = TusharePlugin()
        datahub = DataHub(sources=[tushare])

        result = asyncio.run(datahub.fetch_income("688981.SH"))

        # 验证返回数据
        assert result is not None
        assert len(result) > 0

    def test_fetch_fina_indicator_real(self):
        """通过DataHub获取真实财务指标"""
        from framework.data.hub import DataHub
        from plugins.data_sources.tushare.plugin import TusharePlugin

        tushare = TusharePlugin()
        datahub = DataHub(sources=[tushare])

        result = asyncio.run(datahub.fetch_fina_indicator("688981.SH"))

        # 验证返回数据
        assert result is not None
        assert len(result) > 0
