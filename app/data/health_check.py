"""
数据源健康检查

监控数据源可用性和响应时间
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.data.base import BaseDataSource
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HealthStatus:
    """健康状态"""

    source_name: str
    is_healthy: bool
    response_time_ms: float
    last_check_time: datetime
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class HealthChecker:
    """
    数据源健康检查器

    定期检查数据源可用性，记录响应时间
    """

    def __init__(self, check_interval: int = 60):
        """
        初始化健康检查器

        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self._status_cache: dict[str, HealthStatus] = {}
        self._last_check_time: dict[str, datetime] = {}

    async def check_source(
        self,
        source: BaseDataSource,
        force: bool = False,
    ) -> HealthStatus:
        """
        检查数据源健康状态

        Args:
            source: 数据源实例
            force: 是否强制检查（忽略缓存）

        Returns:
            健康状态
        """
        # 检查缓存
        if not force and source.name in self._status_cache:
            cached = self._status_cache[source.name]
            elapsed = (datetime.now() - cached.last_check_time).total_seconds()
            if elapsed < self.check_interval:
                return cached

        # 执行健康检查
        start_time = time.perf_counter()
        is_healthy = False
        error_message = None

        try:
            is_healthy = await asyncio.wait_for(
                source.health_check(),
                timeout=source.timeout,
            )
        except asyncio.TimeoutError:
            error_message = "Health check timeout"
        except Exception as e:
            error_message = str(e)

        response_time_ms = (time.perf_counter() - start_time) * 1000

        # 构建状态
        status = HealthStatus(
            source_name=source.name,
            is_healthy=is_healthy,
            response_time_ms=response_time_ms,
            last_check_time=datetime.now(),
            error_message=error_message,
            metadata={
                "circuit_breaker_state": (
                    source.circuit_breaker.state.value
                    if hasattr(source, "circuit_breaker")
                    else "unknown"
                ),
            },
        )

        # 更新缓存
        self._status_cache[source.name] = status

        # 记录日志
        if is_healthy:
            logger.info(
                "data_source_health_check_passed",
                source=source.name,
                response_time_ms=response_time_ms,
            )
        else:
            logger.warning(
                "data_source_health_check_failed",
                source=source.name,
                error=error_message,
                response_time_ms=response_time_ms,
            )

        return status

    async def check_all(
        self,
        sources: list[BaseDataSource],
        force: bool = False,
    ) -> dict[str, HealthStatus]:
        """
        检查所有数据源

        Args:
            sources: 数据源列表
            force: 是否强制检查

        Returns:
            数据源名称 -> 健康状态
        """
        results = {}
        tasks = [self.check_source(source, force) for source in sources]

        if tasks:
            statuses = await asyncio.gather(*tasks, return_exceptions=True)
            for source, status_or_exc in zip(sources, statuses):
                if isinstance(status_or_exc, Exception):
                    results[source.name] = HealthStatus(
                        source_name=source.name,
                        is_healthy=False,
                        response_time_ms=0,
                        last_check_time=datetime.now(),
                        error_message=str(status_or_exc),
                    )
                elif isinstance(status_or_exc, HealthStatus):
                    results[source.name] = status_or_exc

        return results

    def get_cached_status(self, source_name: str) -> HealthStatus | None:
        """获取缓存的健康状态"""
        return self._status_cache.get(source_name)

    def get_all_cached_status(self) -> dict[str, HealthStatus]:
        """获取所有缓存的健康状态"""
        return self._status_cache.copy()

    def clear_cache(self) -> None:
        """清除缓存"""
        self._status_cache.clear()

    def get_healthy_sources(
        self,
        sources: list[BaseDataSource],
    ) -> list[BaseDataSource]:
        """
        获取健康的数据源列表

        Args:
            sources: 所有数据源

        Returns:
            健康的数据源列表
        """
        healthy = []
        for source in sources:
            status = self._status_cache.get(source.name)
            if status and status.is_healthy:
                healthy.append(source)
        return healthy
