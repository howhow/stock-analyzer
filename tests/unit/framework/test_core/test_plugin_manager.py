"""测试插件管理器模块"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from framework.core.plugin_manager import PluginManager


class TestPluginManager:
    """测试 PluginManager"""

    def test_init_default(self):
        """测试默认初始化"""
        manager = PluginManager()

        assert manager._config_path is None
        assert manager._plugins == {}
        assert manager._config == {}

    def test_init_with_config_path(self):
        """测试带配置路径初始化"""
        manager = PluginManager(config_path="/path/to/config.yaml")

        assert manager._config_path == Path("/path/to/config.yaml")

    def test_register_plugin(self):
        """测试注册插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.name = "mock"

        manager.register_plugin("mock", mock_plugin)

        assert "mock" in manager._plugins

    def test_get_plugin(self):
        """测试获取插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        manager.register_plugin("mock", mock_plugin)

        result = manager.get_plugin("mock")

        assert result is mock_plugin

    def test_get_plugin_not_found(self):
        """测试获取不存在的插件"""
        manager = PluginManager()

        result = manager.get_plugin("nonexistent")

        assert result is None

    def test_list_plugins(self):
        """测试列出插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        manager.register_plugin("mock", mock_plugin)

        plugins = manager.list_plugins()

        assert "mock" in plugins

    @pytest.mark.asyncio
    async def test_initialize_all(self):
        """测试初始化所有插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.initialize = AsyncMock()
        manager.register_plugin("mock", mock_plugin)

        await manager.initialize_all()

        mock_plugin.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_all(self):
        """测试关闭所有插件"""
        manager = PluginManager()
        mock_plugin = MagicMock()
        mock_plugin.shutdown = AsyncMock()
        manager.register_plugin("mock", mock_plugin)

        await manager.shutdown_all()

        mock_plugin.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_all_no_initialize_method(self):
        """测试初始化无 initialize 方法的插件"""
        manager = PluginManager()
        mock_plugin = MagicMock(spec=[])  # 无 initialize 方法
        manager.register_plugin("mock", mock_plugin)

        # 不应抛出异常
        await manager.initialize_all()
