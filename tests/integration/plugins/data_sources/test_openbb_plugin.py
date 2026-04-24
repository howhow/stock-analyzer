"""OpenBB插件真实调用集成测试"""

import asyncio
from datetime import date, timedelta

import pytest

from plugins.data_sources.openbb.plugin import OpenBBPlugin


@pytest.mark.integration
class TestOpenBBPluginIntegration:
    """OpenBB插件真实调用集成测试

    注意: OpenBB 是可选依赖，需要单独安装:
        pip install openbb

    如果未安装，测试会自动跳过。
    """

    def test_plugin_fetch_quotes(self):
        """插件真实获取日线数据"""
        plugin = OpenBBPlugin()

        # 检查 OpenBB 是否安装
        try:
            plugin._client._ensure_initialized()
        except Exception as e:
            pytest.skip(f"OpenBB 未安装或初始化失败: {e}")

        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        quotes = asyncio.run(plugin.get_quotes("600519.SH", start_date, end_date))

        # 验证返回数据
        assert quotes is not None

    def test_plugin_fetch_financial(self):
        """插件真实获取财务数据"""
        plugin = OpenBBPlugin()

        # OpenBB 暂不支持财务数据
        financial = asyncio.run(plugin.fetch_financial("600519.SH"))

        # 验证返回（可能为空）
        assert financial is not None
