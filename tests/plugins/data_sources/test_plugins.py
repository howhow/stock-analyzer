"""
数据源插件验证测试

验证所有插件可以正确导入和接口实现正确
"""

import pytest

from framework.interfaces.data_source import DataSourceInterface
from framework.models.quote import StandardQuote


# ============================================================
# Import Tests
# ============================================================


class TestPluginImports:
    """插件导入测试"""

    def test_import_tushare_plugin(self):
        """测试导入 TusharePlugin"""
        from plugins.data_sources.tushare import TusharePlugin

        assert TusharePlugin is not None

    def test_import_akshare_plugin(self):
        """测试导入 AKSharePlugin"""
        from plugins.data_sources.akshare import AKSharePlugin

        assert AKSharePlugin is not None

    def test_import_openbb_plugin(self):
        """测试导入 OpenBBPlugin"""
        from plugins.data_sources.openbb import OpenBBPlugin

        assert OpenBBPlugin is not None

    def test_import_local_plugin(self):
        """测试导入 LocalPlugin"""
        from plugins.data_sources.local import LocalPlugin

        assert LocalPlugin is not None


# ============================================================
# Interface Tests
# ============================================================


class TestPluginInterface:
    """插件接口测试"""

    def test_tushare_implements_interface(self):
        """测试 TusharePlugin 实现 DataSourceInterface"""
        from plugins.data_sources.tushare import TusharePlugin

        plugin = TusharePlugin()
        assert isinstance(plugin, DataSourceInterface)
        assert plugin.name == "tushare"
        assert "SH" in plugin.supported_markets

    def test_akshare_implements_interface(self):
        """测试 AKSharePlugin 实现 DataSourceInterface"""
        from plugins.data_sources.akshare import AKSharePlugin

        plugin = AKSharePlugin()
        assert isinstance(plugin, DataSourceInterface)
        assert plugin.name == "akshare"
        assert "SH" in plugin.supported_markets

    def test_openbb_implements_interface(self):
        """测试 OpenBBPlugin 实现 DataSourceInterface"""
        from plugins.data_sources.openbb import OpenBBPlugin

        plugin = OpenBBPlugin()
        assert isinstance(plugin, DataSourceInterface)
        assert plugin.name == "openbb"
        # OpenBB 支持全球市场
        assert len(plugin.supported_markets) >= 4

    def test_local_implements_interface(self):
        """测试 LocalPlugin 实现 DataSourceInterface"""
        from plugins.data_sources.local import LocalPlugin

        plugin = LocalPlugin()
        assert isinstance(plugin, DataSourceInterface)
        assert plugin.name == "local"


# ============================================================
# Mock Data Tests
# ============================================================


class TestPluginWithMockData:
    """使用 Mock 数据测试插件"""

    @pytest.mark.asyncio
    async def test_local_plugin_with_mock_data(self, tmp_path):
        """测试 LocalPlugin 读取 Mock 数据"""
        import pandas as pd
        from datetime import date
        from plugins.data_sources.local import LocalPlugin, LocalPluginConfig

        # 创建测试数据文件
        test_data = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "open": [100.0, 101.0, 102.0],
                "high": [102.0, 103.0, 104.0],
                "low": [99.0, 100.0, 101.0],
                "close": [101.0, 102.0, 103.0],
                "volume": [1000000, 1100000, 1200000],
            }
        )
        test_data.to_csv(tmp_path / "600519_SH.csv", index=False)

        # 创建插件
        config = LocalPluginConfig(data_dir=str(tmp_path))
        plugin = LocalPlugin(config=config)

        # 获取数据
        quotes = await plugin.get_quotes(
            "600519.SH",
            date(2024, 1, 1),
            date(2024, 1, 3),
        )

        assert len(quotes) == 3
        assert quotes[0].close == 101.0
        assert quotes[-1].close == 103.0

    @pytest.mark.asyncio
    async def test_local_health_check(self, tmp_path):
        """测试 LocalPlugin 健康检查"""
        from plugins.data_sources.local import LocalPlugin, LocalPluginConfig

        # 目录存在
        config = LocalPluginConfig(data_dir=str(tmp_path))
        plugin = LocalPlugin(config=config)
        is_healthy = await plugin.health_check()
        assert is_healthy is True

        # 目录不存在
        config2 = LocalPluginConfig(data_dir="/nonexistent/path")
        plugin2 = LocalPlugin(config=config2)
        is_healthy2 = await plugin2.health_check()
        assert is_healthy2 is False
