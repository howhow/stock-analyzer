"""OpenBB插件真实调用集成测试"""

import pytest


@pytest.mark.integration
class TestOpenBBPluginIntegration:
    """OpenBB插件真实调用集成测试"""

    def test_plugin_fetch_quotes(self):
        """插件真实获取日线数据"""
        pytest.skip("OpenBB插件未实现")

    def test_plugin_fetch_financial(self):
        """插件真实获取财务数据"""
        pytest.skip("OpenBB插件未实现")
