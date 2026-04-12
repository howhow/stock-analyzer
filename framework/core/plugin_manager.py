"""
插件管理器模块

动态加载和管理插件。
"""

from pathlib import Path
from typing import Any

import yaml


class PluginManager:
    """
    插件管理器

    职责：
    1. 插件发现：自动发现可用插件
    2. 插件加载：动态加载插件模块
    3. 插件配置：从配置文件读取插件配置
    4. 插件生命周期：初始化、启动、停止
    """

    def __init__(self, config_path: str | Path | None = None):
        """
        初始化插件管理器

        Args:
            config_path: 配置文件路径
        """
        self._config_path = Path(config_path) if config_path else None
        self._plugins: dict[str, Any] = {}
        self._config: dict[str, Any] = {}

    def load_config(self) -> None:
        """加载插件配置"""
        if self._config_path and self._config_path.exists():
            with open(self._config_path) as f:
                self._config = yaml.safe_load(f) or {}

    def register_plugin(self, name: str, plugin: Any) -> None:
        """
        注册插件

        Args:
            name: 插件名称
            plugin: 插件实例
        """
        self._plugins[name] = plugin

    def get_plugin(self, name: str) -> Any | None:
        """
        获取插件

        Args:
            name: 插件名称

        Returns:
            插件实例，如果不存在返回 None
        """
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        """获取已注册的插件列表"""
        return list(self._plugins.keys())

    async def initialize_all(self) -> None:
        """初始化所有插件"""
        for name, plugin in self._plugins.items():
            if hasattr(plugin, "initialize"):
                await plugin.initialize()

    async def shutdown_all(self) -> None:
        """关闭所有插件"""
        for name, plugin in self._plugins.items():
            if hasattr(plugin, "shutdown"):
                await plugin.shutdown()
