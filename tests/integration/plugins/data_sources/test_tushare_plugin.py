"""Tushare插件真实调用集成测试"""

import pytest


@pytest.mark.integration
class TestTusharePluginIntegration:
    """Tushare插件真实调用集成测试"""

    def test_plugin_fetch_quotes(self):
        """插件真实获取日线数据"""
        from plugins.data_sources.tushare.plugin import TusharePlugin

        plugin = TusharePlugin()
        result = plugin.fetch_daily_quotes("688981.SH")

        assert result is not None
        assert len(result) > 0
        assert "close" in result.columns

    def test_plugin_fetch_financial(self):
        """插件真实获取财务数据"""
        from plugins.data_sources.tushare.plugin import TusharePlugin

        plugin = TusharePlugin()
        result = plugin.fetch_financial_data("688981.SH")

        assert result is not None
        assert "pe" in result or "pb" in result or len(result) > 0
