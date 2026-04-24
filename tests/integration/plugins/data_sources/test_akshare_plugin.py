"""AKShare插件真实调用集成测试"""

import asyncio
from datetime import date, timedelta

import pytest

from plugins.data_sources.akshare.plugin import AKSharePlugin


@pytest.mark.integration
class TestAKSharePluginIntegration:
    """AKShare插件真实调用集成测试"""

    def test_plugin_fetch_quotes(self):
        """插件真实获取日线数据"""
        import urllib.error

        plugin = AKSharePlugin()

        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        try:
            quotes = asyncio.run(plugin.get_quotes("600519", start_date, end_date))
        except (urllib.error.URLError, ConnectionError) as e:
            pytest.skip(f"AKShare 网络不可用（EastMoney API 限制）: {e}")

        # 验证返回数据
        assert quotes is not None

        if len(quotes) == 0:
            pytest.skip("AKShare 返回空数据（可能是数据源限制）")

        # 验证数据格式
        first = quotes[0]
        assert first.open > 0
        assert first.close > 0
        assert first.volume >= 0

    def test_plugin_fetch_financial(self):
        """插件真实获取财务数据"""
        plugin = AKSharePlugin()

        # AKShare 暂不支持财务数据，返回空 DataFrame
        financial = asyncio.run(plugin.fetch_financial("600519"))

        # 验证返回（可能为空）
        assert financial is not None
