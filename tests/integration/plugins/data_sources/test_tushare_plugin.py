"""Tushare插件真实调用集成测试"""

import asyncio
from datetime import date, timedelta

import pytest


@pytest.mark.integration
class TestTusharePluginIntegration:
    """Tushare插件真实调用集成测试"""

    def test_plugin_fetch_quotes(self):
        """插件真实获取日线数据"""
        from plugins.data_sources.tushare.plugin import TusharePlugin

        plugin = TusharePlugin()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        result = asyncio.run(plugin.get_quotes("688981.SH", start_date, end_date))

        assert result is not None
        assert len(result) > 0

    def test_plugin_fetch_financial(self):
        """插件真实获取财务数据"""
        from plugins.data_sources.tushare.plugin import TusharePlugin

        plugin = TusharePlugin()
        result = asyncio.run(plugin.fetch_financial("688981.SH"))

        assert result is not None
        assert "pe" in result.columns or "pb" in result.columns or len(result) > 0
