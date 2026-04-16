"""
测试插件管理器模块

更新测试以匹配新的 PluginManager API。
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from framework.core.plugin_manager import PluginManager


class TestPluginManager:
    """测试 PluginManager"""

    def test_init_default(self):
        """测试默认初始化"""
        manager = PluginManager()

        assert manager._config_path == "config/plugins.yaml"
        assert manager._plugins is not None

    def test_init_with_config_path(self):
        """测试带配置路径初始化"""
        manager = PluginManager(config_path="/path/to/config.yaml")

        assert manager._config_path == "/path/to/config.yaml"

    def test_register_plugin(self):
        """测试注册插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.name = "mock"

        manager.register_plugin(mock_plugin, "report", "mock")

        assert "mock" in manager._plugins["report"]

    def test_get_plugin(self):
        """测试获取插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.name = "mock"
        manager.register_plugin(mock_plugin, "report", "mock")

        result = manager.get_plugin("mock", "report")

        assert result is mock_plugin

    def test_get_plugin_not_found(self):
        """测试获取不存在的插件"""
        manager = PluginManager()

        result = manager.get_plugin("nonexistent", "report")

        assert result is None

    def test_list_plugins(self):
        """测试列出插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.name = "mock"
        manager.register_plugin(mock_plugin, "report", "mock")

        plugins = manager.list_plugins("report")

        assert "mock" in plugins

    def test_list_plugins_all_types(self):
        """测试列出所有类型插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.name = "mock"
        manager.register_plugin(mock_plugin, "report", "mock")

        plugins = manager.list_plugins()

        assert "mock" in plugins

    def test_discover_plugins(self):
        """测试发现插件"""
        manager = PluginManager()
        discovered = manager.discover_plugins("plugins")

        assert isinstance(discovered, list)
        assert len(discovered) > 0

    def test_load_plugin_from_entrypoint(self):
        """测试从入口点加载插件"""
        manager = PluginManager()

        plugin = manager.load_plugin_from_entrypoint(
            "plugins.reports.markdown:MarkdownReportPlugin"
        )

        assert plugin is not None
        assert plugin.name == "markdown"

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        manager = PluginManager()

        health = await manager.health_check()

        assert isinstance(health, dict)

    def test_enable_disable_plugin(self):
        """测试启用/禁用插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.name = "mock"
        manager.register_plugin(mock_plugin, "report", "mock")

        # 禁用
        result = manager.disable_plugin("mock", "report")
        assert result is True

        # 启用
        result = manager.enable_plugin("mock", "report")
        assert result is True
