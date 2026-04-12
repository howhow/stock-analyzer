"""
数据核心模块

统一数据管理、路由和缓存。
"""

from datetime import date
from typing import Any

from framework.interfaces.data_source import DataSourceInterface
from framework.models.quote import StandardQuote


class DataCore:
    """
    数据核心

    职责：
    1. 数据路由：根据优先级选择数据源
    2. 数据缓存：Redis多级缓存
    3. 数据质量：完整性、合理性检查
    4. 数据降级：多源降级策略
    """

    # 数据源优先级（默认）
    DEFAULT_PRIORITY = ["tushare", "akshare", "openbb", "local"]

    def __init__(
        self,
        plugins: dict[str, DataSourceInterface] | None = None,
        priority: list[str] | None = None,
        cache_ttl: int = 1800,  # 30分钟
    ):
        """
        初始化数据核心

        Args:
            plugins: 数据源插件字典
            priority: 数据源优先级
            cache_ttl: 缓存TTL（秒）
        """
        self._plugins = plugins or {}
        self._priority = priority or self.DEFAULT_PRIORITY.copy()
        self._cache_ttl = cache_ttl

    def register_plugin(self, plugin: DataSourceInterface) -> None:
        """
        注册数据源插件

        Args:
            plugin: 数据源插件实例
        """
        self._plugins[plugin.name] = plugin

    async def get_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
        source: str | None = None,
    ) -> list[StandardQuote]:
        """
        获取行情数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            source: 指定数据源（可选）

        Returns:
            标准行情数据列表

        Raises:
            AllDataSourcesFailedError: 所有数据源都失败
        """
        # TODO: 实现数据路由和缓存逻辑
        raise NotImplementedError("DataCore.get_quotes not implemented yet")

    async def health_check(self) -> dict[str, bool]:
        """
        检查所有数据源健康状态

        Returns:
            数据源健康状态字典
        """
        results = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = await plugin.health_check()
            except Exception:
                results[name] = False
        return results

    def get_available_sources(self) -> list[str]:
        """获取可用数据源列表"""
        return list(self._plugins.keys())
