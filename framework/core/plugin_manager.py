"""
插件管理器

负责动态加载和管理所有插件（数据源、AI提供商、报告等）。
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml
from structlog import get_logger

logger = get_logger(__name__)


class PluginManager:
    """
    插件管理器
    
    职责：
    1. 动态加载插件
    2. 配置驱动
    3. 生命周期管理
    """
    
    def __init__(self, config_path: str = "config/plugins.yaml"):
        """
        初始化插件管理器
        
        Args:
            config_path: 插件配置文件路径
        """
        self._config_path = config_path
        self._plugins: dict[str, dict[str, Any]] = {
            "data_source": {},
            "ai_provider": {},
            "report": {},
            "indicator": {},
            "strategy": {},
        }
        self._config: dict[str, Any] = {}
    
    def load_config(self) -> None:
        """加载配置文件"""
        config_file = Path(self._config_path)
        if not config_file.exists():
            logger.warning("plugin_config_not_found", path=self._config_path)
            return
        
        with open(config_file) as f:
            self._config = yaml.safe_load(f) or {}
        
        logger.info("plugin_config_loaded", path=self._config_path)
    
    def load_plugins(self) -> None:
        """从配置加载所有插件"""
        if not self._config:
            self.load_config()
        
        for plugin_type in ["data_sources", "ai_providers", "reports"]:
            plugins_config = self._config.get(plugin_type, {})
            for name, config in plugins_config.items():
                if config.get("enabled", True):
                    try:
                        entrypoint = config.get("entrypoint")
                        if entrypoint:
                            plugin = self.load_plugin_from_entrypoint(entrypoint)
                            plugin_config = config.get("config", {})
                            self.register_plugin(
                                plugin,
                                plugin_type.rstrip("s"),  # data_sources -> data_source
                                name,
                                plugin_config,
                            )
                            logger.info(
                                "plugin_loaded",
                                name=name,
                                type=plugin_type,
                            )
                    except Exception as e:
                        logger.error(
                            "plugin_load_failed",
                            name=name,
                            type=plugin_type,
                            error=str(e),
                        )
    
    def register_plugin(
        self,
        plugin: Any,
        plugin_type: str,
        name: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """
        注册插件
        
        Args:
            plugin: 插件实例
            plugin_type: 插件类型 (data_source, ai_provider, report)
            name: 插件名称（可选，默认使用 plugin.name）
            config: 插件配置
        """
        plugin_name = name or getattr(plugin, "name", plugin.__class__.__name__)
        
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}
        
        self._plugins[plugin_type][plugin_name] = {
            "instance": plugin,
            "config": config or {},
            "enabled": True,
        }
        
        logger.debug("plugin_registered", name=plugin_name, type=plugin_type)
    
    def get_plugin(self, name: str, plugin_type: str) -> Any | None:
        """
        获取插件
        
        Args:
            name: 插件名称
            plugin_type: 插件类型
            
        Returns:
            插件实例，不存在返回 None
        """
        plugins = self._plugins.get(plugin_type, {})
        plugin_info = plugins.get(name)
        if plugin_info and plugin_info.get("enabled", True):
            return plugin_info.get("instance")
        return None
    
    def list_plugins(self, plugin_type: str | None = None) -> list[str]:
        """
        列出插件
        
        Args:
            plugin_type: 插件类型（可选，返回所有类型）
            
        Returns:
            插件名称列表
        """
        if plugin_type:
            return list(self._plugins.get(plugin_type, {}).keys())
        
        all_plugins: list[str] = []
        for ptype, plugins in self._plugins.items():
            all_plugins.extend(plugins.keys())
        return all_plugins
    
    def discover_plugins(self, plugin_dir: str = "plugins") -> list[dict]:
        """
        自动发现插件
        
        Args:
            plugin_dir: 插件目录
            
        Returns:
            发现的插件列表
        """
        discovered: list[dict] = []
        plugin_path = Path(plugin_dir)
        
        if not plugin_path.exists():
            return discovered
        
        # 扫描插件类型目录
        for plugin_type_dir in plugin_path.iterdir():
            if not plugin_type_dir.is_dir():
                continue
            if plugin_type_dir.name.startswith("_"):
                continue
            
            plugin_type = plugin_type_dir.name  # data_sources, ai_providers, reports
            
            # 扫描具体插件
            for plugin_subdir in plugin_type_dir.iterdir():
                if not plugin_subdir.is_dir():
                    continue
                if plugin_subdir.name.startswith("_"):
                    continue
                
                # 检查是否有 __init__.py
                init_file = plugin_subdir / "__init__.py"
                if init_file.exists():
                    discovered.append({
                        "name": plugin_subdir.name,
                        "type": plugin_type,
                        "path": str(plugin_subdir),
                        "entrypoint": f"{plugin_dir}.{plugin_type}.{plugin_subdir.name}",
                    })
        
        logger.info("plugins_discovered", count=len(discovered))
        return discovered
    
    def load_plugin_from_entrypoint(self, entrypoint: str) -> Any:
        """
        从入口点加载插件
        
        Args:
            entrypoint: 入口点字符串
                格式: "module.path:ClassName"
                示例: "plugins.data_sources.tushare:TusharePlugin"
                
        Returns:
            插件实例
        """
        if ":" not in entrypoint:
            raise ValueError(f"Invalid entrypoint format: {entrypoint}")
        
        module_path, class_name = entrypoint.rsplit(":", 1)
        
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            return plugin_class()
        except ImportError as e:
            raise ImportError(f"Failed to import module {module_path}: {e}") from e
        except AttributeError as e:
            raise AttributeError(
                f"Class {class_name} not found in {module_path}: {e}"
            ) from e
    
    async def health_check(self) -> dict[str, dict[str, bool]]:
        """
        检查所有插件健康状态
        
        Returns:
            按类型分组的健康状态
        """
        health_status: dict[str, dict[str, bool]] = {}
        
        for plugin_type, plugins in self._plugins.items():
            health_status[plugin_type] = {}
            for name, plugin_info in plugins.items():
                if not plugin_info.get("enabled", True):
                    health_status[plugin_type][name] = False
                    continue
                
                plugin = plugin_info.get("instance")
                if hasattr(plugin, "health_check"):
                    try:
                        is_healthy = await plugin.health_check()
                        health_status[plugin_type][name] = is_healthy
                    except Exception as e:
                        logger.warning(
                            "health_check_failed",
                            name=name,
                            type=plugin_type,
                            error=str(e),
                        )
                        health_status[plugin_type][name] = False
                else:
                    health_status[plugin_type][name] = True
        
        return health_status
    
    def reload_plugin(self, name: str, plugin_type: str) -> bool:
        """
        重新加载插件（热更新）
        
        Args:
            name: 插件名称
            plugin_type: 插件类型
            
        Returns:
            是否成功
        """
        try:
            plugins = self._plugins.get(plugin_type, {})
            plugin_info = plugins.get(name)
            if not plugin_info:
                return False
            
            # 获取原来的入口点
            config = self._config.get(f"{plugin_type}s", {}).get(name, {})
            entrypoint = config.get("entrypoint")
            
            if entrypoint:
                # 重新加载模块
                module_path = entrypoint.rsplit(":", 1)[0]
                module = importlib.import_module(module_path)
                importlib.reload(module)
                
                # 重新创建实例
                new_plugin = self.load_plugin_from_entrypoint(entrypoint)
                plugin_info["instance"] = new_plugin
                
                logger.info("plugin_reloaded", name=name, type=plugin_type)
                return True
            
            return False
        except Exception as e:
            logger.error(
                "plugin_reload_failed",
                name=name,
                type=plugin_type,
                error=str(e),
            )
            return False
    
    def enable_plugin(self, name: str, plugin_type: str) -> bool:
        """启用插件"""
        plugins = self._plugins.get(plugin_type, {})
        if name in plugins:
            plugins[name]["enabled"] = True
            return True
        return False
    
    def disable_plugin(self, name: str, plugin_type: str) -> bool:
        """禁用插件"""
        plugins = self._plugins.get(plugin_type, {})
        if name in plugins:
            plugins[name]["enabled"] = False
            return True
        return False


# 全局插件管理器实例
_plugin_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
