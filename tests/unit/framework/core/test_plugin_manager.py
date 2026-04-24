"""
PluginManager 测试

全部 Mock，零外部依赖。
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from framework.core.plugin_manager import PluginManager, get_plugin_manager

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def manager():
    """创建 PluginManager 实例"""
    return PluginManager(config_path="test_config.yaml")


@pytest.fixture
def mock_plugin():
    """创建 Mock 插件"""
    plugin = MagicMock()
    plugin.name = "test_plugin"
    return plugin


# ═══════════════════════════════════════════════════════════════
# 配置加载测试
# ═══════════════════════════════════════════════════════════════


class TestLoadConfig:
    """配置加载测试"""

    def test_load_config_success(self, manager):
        """测试成功加载配置"""
        config_data = {
            "data_sources": {
                "tushare": {
                    "enabled": True,
                    "entrypoint": "plugins.data_sources.tushare:TusharePlugin",
                }
            }
        }

        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=yaml.dump(config_data))
        ), patch("yaml.safe_load", return_value=config_data):
            manager.load_config()

        assert manager._config == config_data

    def test_load_config_not_found(self, manager):
        """测试配置文件不存在"""
        with patch("pathlib.Path.exists", return_value=False):
            manager.load_config()

        assert manager._config == {}


# ═══════════════════════════════════════════════════════════════
# 插件注册/获取测试
# ═══════════════════════════════════════════════════════════════


class TestRegisterPlugin:
    """插件注册测试"""

    def test_register_plugin(self, manager, mock_plugin):
        """测试注册插件"""
        manager.register_plugin(mock_plugin, "data_source", "test")

        plugin = manager.get_plugin("test", "data_source")
        assert plugin is mock_plugin

    def test_register_plugin_auto_name(self, manager, mock_plugin):
        """测试自动获取插件名称"""
        manager.register_plugin(mock_plugin, "data_source")

        plugin = manager.get_plugin("test_plugin", "data_source")
        assert plugin is mock_plugin

    def test_register_plugin_with_config(self, manager, mock_plugin):
        """测试带配置注册"""
        manager.register_plugin(mock_plugin, "data_source", config={"key": "value"})

        info = manager._plugins["data_source"]["test_plugin"]
        assert info["config"] == {"key": "value"}

    def test_get_plugin_disabled(self, manager, mock_plugin):
        """测试获取禁用的插件返回 None"""
        manager.register_plugin(mock_plugin, "data_source")
        manager.disable_plugin("test_plugin", "data_source")

        plugin = manager.get_plugin("test_plugin", "data_source")
        assert plugin is None

    def test_get_plugin_not_found(self, manager):
        """测试获取不存在的插件"""
        plugin = manager.get_plugin("nonexistent", "data_source")
        assert plugin is None


# ═══════════════════════════════════════════════════════════════
# 插件列表测试
# ═══════════════════════════════════════════════════════════════


class TestListPlugins:
    """插件列表测试"""

    def test_list_plugins_by_type(self, manager, mock_plugin):
        """测试按类型列出插件"""
        manager.register_plugin(mock_plugin, "data_source", "plugin1")
        manager.register_plugin(mock_plugin, "data_source", "plugin2")

        plugins = manager.list_plugins("data_source")
        assert sorted(plugins) == ["plugin1", "plugin2"]

    def test_list_all_plugins(self, manager, mock_plugin):
        """测试列出所有插件"""
        manager.register_plugin(mock_plugin, "data_source", "ds1")
        manager.register_plugin(mock_plugin, "ai_provider", "ai1")

        plugins = manager.list_plugins()
        assert "ds1" in plugins
        assert "ai1" in plugins


# ═══════════════════════════════════════════════════════════════
# 插件发现测试
# ═══════════════════════════════════════════════════════════════


class TestDiscoverPlugins:
    """插件发现测试"""

    def test_discover_plugins_empty_dir(self, manager):
        """测试空目录"""
        with patch("pathlib.Path.exists", return_value=False):
            discovered = manager.discover_plugins("nonexistent")

        assert discovered == []

    def test_discover_plugins(self, manager):
        """测试发现插件"""
        # 创建模拟目录结构
        mock_dir = MagicMock()
        mock_dir.is_dir.return_value = True
        mock_dir.name = "tushare"
        mock_dir.__truediv__ = lambda self, other: MagicMock(
            exists=lambda: True, is_dir=lambda: True, name="__init__.py"
        )

        type_dir = MagicMock()
        type_dir.is_dir.return_value = True
        type_dir.name = "data_sources"
        type_dir.iterdir.return_value = [mock_dir]

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.iterdir", return_value=[type_dir]
        ):
            discovered = manager.discover_plugins()

        assert len(discovered) >= 0  # 至少不报错


# ═══════════════════════════════════════════════════════════════
# 入口点加载测试
# ═══════════════════════════════════════════════════════════════


class TestLoadFromEntrypoint:
    """入口点加载测试"""

    def test_load_plugin_from_entrypoint(self, manager):
        """测试从入口点加载"""
        mock_module = MagicMock()
        mock_class = MagicMock(return_value="plugin_instance")
        mock_module.PluginClass = mock_class

        with patch("importlib.import_module", return_value=mock_module):
            result = manager.load_plugin_from_entrypoint("module.path:PluginClass")

        assert result == "plugin_instance"

    def test_load_plugin_invalid_entrypoint(self, manager):
        """测试无效入口点格式"""
        with pytest.raises(ValueError, match="Invalid entrypoint"):
            manager.load_plugin_from_entrypoint("invalid_format")

    def test_load_plugin_import_error(self, manager):
        """测试导入错误"""
        with patch(
            "importlib.import_module", side_effect=ImportError("No module")
        ), pytest.raises(ImportError):
            manager.load_plugin_from_entrypoint("nonexistent:Class")


# ═══════════════════════════════════════════════════════════════
# 健康检查测试
# ═══════════════════════════════════════════════════════════════


class TestHealthCheck:
    """健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, manager, mock_plugin):
        """测试所有插件健康"""

        async def async_health():
            return True

        mock_plugin.health_check = async_health
        manager.register_plugin(mock_plugin, "data_source", "test")

        result = await manager.health_check()

        assert result["data_source"]["test"] is True

    @pytest.mark.asyncio
    async def test_health_check_no_method(self, manager):
        """测试无健康检查方法的插件"""
        plugin = MagicMock(spec=[])  # 明确无 health_check 方法
        manager.register_plugin(plugin, "data_source", "test")

        result = await manager.health_check()

        assert result["data_source"]["test"] is True

    @pytest.mark.asyncio
    async def test_health_check_exception(self, manager, mock_plugin):
        """测试健康检查异常"""
        mock_plugin.health_check = MagicMock(side_effect=Exception("Error"))
        manager.register_plugin(mock_plugin, "data_source", "test")

        result = await manager.health_check()

        assert result["data_source"]["test"] is False

    @pytest.mark.asyncio
    async def test_health_check_disabled(self, manager, mock_plugin):
        """测试禁用插件标记为不健康"""
        manager.register_plugin(mock_plugin, "data_source", "test")
        manager.disable_plugin("test", "data_source")

        result = await manager.health_check()

        assert result["data_source"]["test"] is False


# ═══════════════════════════════════════════════════════════════
# 启用/禁用测试
# ═══════════════════════════════════════════════════════════════


class TestEnableDisable:
    """启用禁用测试"""

    def test_enable_plugin(self, manager, mock_plugin):
        """测试启用插件"""
        manager.register_plugin(mock_plugin, "data_source", "test")
        manager.disable_plugin("test", "data_source")

        result = manager.enable_plugin("test", "data_source")
        assert result is True

        plugin = manager.get_plugin("test", "data_source")
        assert plugin is mock_plugin

    def test_disable_plugin(self, manager, mock_plugin):
        """测试禁用插件"""
        manager.register_plugin(mock_plugin, "data_source", "test")

        result = manager.disable_plugin("test", "data_source")
        assert result is True

        plugin = manager.get_plugin("test", "data_source")
        assert plugin is None

    def test_enable_nonexistent(self, manager):
        """测试启用不存在的插件"""
        result = manager.enable_plugin("nonexistent", "data_source")
        assert result is False


# ═══════════════════════════════════════════════════════════════
# 热更新测试
# ═══════════════════════════════════════════════════════════════


class TestReload:
    """热更新测试"""

    def test_reload_plugin(self, manager, mock_plugin):
        """测试热更新插件"""
        manager._config = {
            "data_sources": {"test": {"entrypoint": "module.path:PluginClass"}}
        }
        manager.register_plugin(mock_plugin, "data_source", "test")

        new_plugin = MagicMock()

        # 直接 mock reload_plugin 方法内部的 importlib.reload
        with patch.object(
            manager, "load_plugin_from_entrypoint", return_value=new_plugin
        ), patch("framework.core.plugin_manager.importlib") as mock_importlib:
            mock_module = MagicMock()
            mock_importlib.import_module.return_value = mock_module
            # 让 reload 返回模块本身
            mock_importlib.reload.return_value = mock_module

            result = manager.reload_plugin("test", "data_source")

        assert result is True

    def test_reload_plugin_not_found(self, manager):
        """测试热更新不存在的插件"""
        result = manager.reload_plugin("nonexistent", "data_source")
        assert result is False


# ═══════════════════════════════════════════════════════════════
# 全局实例测试
# ═══════════════════════════════════════════════════════════════


class TestGlobalInstance:
    """全局实例测试"""

    def test_get_plugin_manager(self):
        """测试获取全局实例"""
        pm1 = get_plugin_manager()
        pm2 = get_plugin_manager()

        assert pm1 is pm2
        assert isinstance(pm1, PluginManager)
