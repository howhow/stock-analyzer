"""
数据核心模块

统一数据管理、路由和缓存。
"""

from datetime import date
from typing import Any

from app.core.cache import CacheManager
from app.utils.logger import get_logger
from config import settings
from framework.interfaces.data_source import DataSourceInterface
from framework.models.quote import StandardQuote

logger = get_logger(__name__)

# 导入异常类（唯一真实源：app/core/exceptions.py）
from app.core.exceptions import (
    AllDataSourcesFailedError,
    DataSourceNotFoundError,
    NoDataError,
)


# ============================================================================
# 数据核心
# ============================================================================


class DataCore:
    """
    数据核心

    职责：
    1. 数据路由：根据优先级选择数据源
    2. 数据缓存：Redis多级缓存
    3. 数据质量：完整性、合理性检查
    4. 数据降级：多源降级策略

    Example:
        >>> data_core = DataCore(plugins={"tushare": tushare_plugin})
        >>> quotes = await data_core.get_quotes("600519.SH", date(2024, 1, 1), date(2024, 1, 31))
    """

    # 数据源优先级（默认）
    DEFAULT_PRIORITY = ["tushare", "akshare", "openbb", "local"]

    def __init__(
        self,
        plugins: dict[str, DataSourceInterface] | None = None,
        priority: list[str] | None = None,
        cache_ttl: int | None = None,
        cache_manager: CacheManager | None = None,
    ):
        """
        初始化数据核心

        Args:
            plugins: 数据源插件字典 {name: plugin_instance}
            priority: 数据源优先级列表
            cache_ttl: 缓存TTL（秒），默认使用 settings.cache_ttl_daily
            cache_manager: 缓存管理器实例（可选，默认创建新实例）
        """
        self._plugins = plugins or {}
        self._priority = priority or self.DEFAULT_PRIORITY.copy()
        self._cache_ttl = cache_ttl or settings.cache_ttl_daily
        self._cache = cache_manager or CacheManager(default_ttl=self._cache_ttl)

        # 数据源状态追踪
        self._source_status: dict[str, dict[str, Any]] = {
            name: {"healthy": True, "last_check": None, "failures": 0}
            for name in self._plugins
        }

        logger.info(
            "data_core_initialized",
            plugins=list(self._plugins.keys()),
            priority=self._priority,
            cache_ttl=self._cache_ttl,
        )

    def register_plugin(self, plugin: DataSourceInterface) -> None:
        """
        注册数据源插件

        Args:
            plugin: 数据源插件实例
        """
        self._plugins[plugin.name] = plugin
        self._source_status[plugin.name] = {
            "healthy": True,
            "last_check": None,
            "failures": 0,
        }
        logger.info("plugin_registered", source=plugin.name)

    # ========================================================================
    # 主要接口
    # ========================================================================

    async def get_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
        source: str | None = None,
    ) -> list[StandardQuote]:
        """
        获取行情数据

        数据获取流程：
        1. 检查缓存，命中则返回
        2. 如果指定 source，使用指定数据源
        3. 否则按优先级依次尝试数据源
        4. 成功则写入缓存并返回
        5. 失败则降级到下一个数据源
        6. 全部失败则抛出 AllDataSourcesFailedError

        Args:
            stock_code: 股票代码（如 '600519.SH'）
            start_date: 开始日期
            end_date: 结束日期
            source: 指定数据源（可选）

        Returns:
            标准行情数据列表

        Raises:
            AllDataSourcesFailedError: 所有数据源都失败
            DataSourceNotFoundError: 指定的数据源不存在
            NoDataError: 所有数据源返回空数据
        """
        cache_key = self._make_cache_key(stock_code, start_date, end_date)

        # 1. 检查缓存
        cached = await self._cache.get(cache_key)
        if cached is not None:
            logger.debug(
                "cache_hit",
                cache_key=cache_key,
                count=len(cached),
            )
            return [StandardQuote.model_validate(q) for q in cached]

        logger.debug(
            "cache_miss",
            cache_key=cache_key,
            stock_code=stock_code,
            source=source,
        )

        # 2. 获取数据
        quotes, actual_source = await self._try_sources(
            stock_code, start_date, end_date, source
        )

        # 3. 数据质量检查
        quotes = self._check_data_quality(quotes, actual_source)

        # 4. 写入缓存
        await self._cache.set(cache_key, [q.model_dump() for q in quotes])

        logger.info(
            "quotes_fetched",
            stock_code=stock_code,
            source=actual_source,
            count=len(quotes),
            cache_key=cache_key,
        )

        return quotes

    async def get_realtime_quote(
        self,
        stock_code: str,
        source: str | None = None,
    ) -> StandardQuote | None:
        """
        获取实时行情数据

        Args:
            stock_code: 股票代码
            source: 指定数据源（可选）

        Returns:
            标准行情数据（单条），如果不支持或无数据则返回 None

        Note:
            实时行情不缓存，每次都从数据源获取
        """
        # 确定数据源顺序
        sources_to_try = self._get_source_order(source)

        for src_name in sources_to_try:
            plugin = self._plugins.get(src_name)
            if plugin is None:
                continue

            try:
                quote = await plugin.get_realtime_quote(stock_code)
                if quote is not None:
                    # 添加质量评分
                    quote.quality_score = 1.0
                    quote.completeness = 1.0 if quote.is_complete() else 0.8

                    logger.debug(
                        "realtime_quote_fetched",
                        stock_code=stock_code,
                        source=src_name,
                    )
                    return quote

            except Exception as e:
                logger.warning(
                    "realtime_quote_failed",
                    stock_code=stock_code,
                    source=src_name,
                    error=str(e),
                )
                continue

        logger.warning(
            "realtime_quote_no_data",
            stock_code=stock_code,
            sources_tried=sources_to_try,
        )
        return None

    async def get_source_status(self) -> dict[str, dict[str, Any]]:
        """
        获取所有数据源状态

        Returns:
            数据源状态字典 {source_name: status_dict}

            每个状态包含：
            - healthy: 是否健康
            - last_check: 最后检查时间
            - failures: 连续失败次数
            - available: 插件是否已注册
        """
        result: dict[str, dict[str, Any]] = {}

        for name in self._priority:
            if name not in self._plugins:
                result[name] = {
                    "healthy": False,
                    "available": False,
                    "last_check": None,
                    "failures": 0,
                }
                continue

            # 执行健康检查
            try:
                plugin = self._plugins[name]
                is_healthy = await plugin.health_check()

                # 更新状态
                self._source_status[name]["healthy"] = is_healthy
                self._source_status[name]["last_check"] = date.today().isoformat()
                if is_healthy:
                    self._source_status[name]["failures"] = 0
                else:
                    self._source_status[name]["failures"] += 1

                result[name] = {
                    **self._source_status[name],
                    "available": True,
                }

            except Exception as e:
                logger.warning(
                    "health_check_failed",
                    source=name,
                    error=str(e),
                )
                result[name] = {
                    "healthy": False,
                    "available": True,
                    "last_check": None,
                    "failures": self._source_status[name]["failures"] + 1,
                    "error": str(e),
                }

        return result

    async def clear_cache(
        self,
        stock_code: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> int:
        """
        清除缓存

        Args:
            stock_code: 股票代码（可选，不指定则清除所有）
            start_date: 开始日期（可选，需要 stock_code）
            end_date: 结束日期（可选，需要 stock_code）

        Returns:
            清除的缓存条目数（Redis 不支持精确计数，返回 0 或 1）

        Note:
            - 只清除 Redis 缓存，本地缓存会自动过期
            - 如果只指定 stock_code，清除该股票的所有缓存
        """
        count = 0

        if stock_code and start_date and end_date:
            # 清除特定缓存
            cache_key = self._make_cache_key(stock_code, start_date, end_date)
            await self._cache.delete(cache_key)
            count = 1
            logger.info(
                "cache_cleared",
                cache_key=cache_key,
            )
        elif stock_code:
            # 清除该股票的所有缓存（需要模式匹配，Redis 支持）
            # 简化实现：清除本地缓存
            await self._cache.clear_local()
            logger.info(
                "local_cache_cleared",
                stock_code=stock_code,
            )
        else:
            # 清除所有本地缓存
            await self._cache.clear_local()
            logger.info("all_local_cache_cleared")

        return count

    def get_available_sources(self) -> list[str]:
        """
        获取可用数据源列表

        Returns:
            数据源名称列表
        """
        return list(self._plugins.keys())

    async def health_check(self) -> dict[str, bool]:
        """
        检查所有数据源健康状态

        Returns:
            数据源健康状态字典 {source_name: is_healthy}
        """
        results: dict[str, bool] = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = await plugin.health_check()
            except Exception:
                results[name] = False
        return results

    # ========================================================================
    # 内部方法
    # ========================================================================

    async def _try_sources(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
        source: str | None = None,
    ) -> tuple[list[StandardQuote], str]:
        """
        尝试从多个数据源获取数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            source: 指定数据源（可选）

        Returns:
            (行情数据列表, 实际使用的数据源名称)

        Raises:
            AllDataSourcesFailedError: 所有数据源都失败
            DataSourceNotFoundError: 指定的数据源不存在
            NoDataError: 所有数据源返回空数据
        """
        # 确定尝试顺序
        sources_to_try = self._get_source_order(source)

        if not sources_to_try:
            raise DataSourceNotFoundError(
                source or "any",
                list(self._plugins.keys()),
            )

        # 记录失败原因
        failures: dict[str, str] = {}
        last_quotes: list[StandardQuote] | None = None
        last_source: str | None = None

        for src_name in sources_to_try:
            plugin = self._plugins.get(src_name)
            if plugin is None:
                failures[src_name] = "Plugin not registered"
                continue

            try:
                logger.debug(
                    "trying_source",
                    stock_code=stock_code,
                    source=src_name,
                )

                quotes = await plugin.get_quotes(stock_code, start_date, end_date)

                if quotes:
                    # 成功获取数据
                    # 更新数据源状态
                    self._source_status[src_name]["failures"] = 0
                    self._source_status[src_name]["healthy"] = True

                    return quotes, src_name

                # 空数据，记录但继续尝试
                failures[src_name] = "No data returned"
                last_quotes = quotes
                last_source = src_name

                logger.warning(
                    "source_no_data",
                    stock_code=stock_code,
                    source=src_name,
                )

            except Exception as e:
                error_msg = str(e)
                failures[src_name] = error_msg

                # 更新失败计数
                self._source_status[src_name]["failures"] += 1
                self._source_status[src_name]["healthy"] = False

                logger.warning(
                    "source_failed",
                    stock_code=stock_code,
                    source=src_name,
                    error=error_msg,
                    consecutive_failures=self._source_status[src_name]["failures"],
                )

        # 所有数据源都尝试过了
        if last_quotes is not None and last_source:
            # 有空数据返回，不算完全失败
            raise NoDataError(stock_code, start_date, end_date, last_source)

        raise AllDataSourcesFailedError(
            stock_code, start_date, end_date, failures
        )

    def _get_source_order(self, source: str | None = None) -> list[str]:
        """
        获取数据源尝试顺序

        Args:
            source: 指定数据源

        Returns:
            数据源名称列表

        Raises:
            DataSourceNotFoundError: 指定的数据源不存在
        """
        if source:
            if source not in self._plugins:
                raise DataSourceNotFoundError(source, list(self._plugins.keys()))
            return [source]

        # 按优先级排序，跳过未注册的数据源
        # 可以在这里加入熔断逻辑：跳过连续失败过多的数据源
        result = []
        for name in self._priority:
            if name in self._plugins:
                # 熔断检查：连续失败超过阈值则跳过
                status = self._source_status.get(name, {})
                if status.get("failures", 0) < settings.circuit_breaker_threshold:
                    result.append(name)

        # 如果所有高优先级数据源都被熔断，强制使用第一个可用数据源
        if not result and self._plugins:
            result = [self._priority[0]] if self._priority[0] in self._plugins else list(self._plugins.keys())[:1]

        return result

    def _check_data_quality(
        self,
        quotes: list[StandardQuote],
        source: str,
    ) -> list[StandardQuote]:
        """
        检查数据质量

        质量检查包括：
        1. 完整性检查：必填字段是否存在
        2. 合理性检查：价格逻辑是否正确
        3. 计算完整度评分

        Args:
            quotes: 行情数据列表
            source: 数据源名称

        Returns:
            带质量评分的行情数据列表
        """
        if not quotes:
            return quotes

        checked_quotes: list[StandardQuote] = []

        for quote in quotes:
            # 设置数据源
            quote.source = source

            # 计算完整度
            completeness = self._calculate_completeness(quote)
            quote.completeness = completeness

            # 计算质量评分
            quality_score = self._calculate_quality_score(quote)
            quote.quality_score = quality_score

            # 记录质量问题
            if quality_score < 0.7:
                logger.debug(
                    "low_quality_data",
                    code=quote.code,
                    date=str(quote.trade_date),
                    completeness=completeness,
                    quality_score=quality_score,
                )

            checked_quotes.append(quote)

        # 计算整体质量统计
        avg_quality = sum(q.quality_score for q in checked_quotes) / len(checked_quotes)
        avg_completeness = sum(q.completeness for q in checked_quotes) / len(checked_quotes)

        logger.debug(
            "data_quality_checked",
            source=source,
            count=len(checked_quotes),
            avg_quality=round(avg_quality, 3),
            avg_completeness=round(avg_completeness, 3),
        )

        return checked_quotes

    def _calculate_completeness(self, quote: StandardQuote) -> float:
        """
        计算数据完整度

        完整度基于：
        - 必填字段：code, trade_date, close (必须存在)
        - 价格字段：open, high, low (可选但重要)
        - 成交字段：volume, amount (可选)

        Args:
            quote: 行情数据

        Returns:
            完整度评分 (0-1)
        """
        # 必填字段检查
        if not all([quote.code, quote.trade_date, quote.close is not None]):
            return 0.0

        # 价格字段权重：40%
        price_fields = ["open", "high", "low", "adj_close"]
        price_score = sum(
            1 for f in price_fields if getattr(quote, f, None) is not None
        ) / len(price_fields)

        # 成交字段权重：30%
        volume_fields = ["volume", "amount", "turnover_rate"]
        volume_score = sum(
            1 for f in volume_fields if getattr(quote, f, None) is not None
        ) / len(volume_fields)

        # 计算总分
        completeness = 0.3 + price_score * 0.4 + volume_score * 0.3

        return round(completeness, 3)

    def _calculate_quality_score(self, quote: StandardQuote) -> float:
        """
        计算数据质量评分

        质量评分基于：
        - 完整度：50%
        - 逻辑合理性：30%
        - 数据来源可信度：20%

        Args:
            quote: 行情数据

        Returns:
            质量评分 (0-1)
        """
        score = 0.0

        # 完整度贡献
        score += quote.completeness * 0.5

        # 逻辑合理性贡献
        if quote.is_valid():
            score += 0.3
        elif quote.open is None or quote.high is None or quote.low is None:
            # 部分价格缺失，扣分
            score += 0.1

        # 数据源可信度（根据数据源名称）
        source_trust = {
            "tushare": 0.2,
            "akshare": 0.18,
            "openbb": 0.15,
            "local": 0.1,
        }.get(quote.source, 0.15)

        score += source_trust

        return round(min(score, 1.0), 3)

    def _make_cache_key(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> str:
        """
        生成缓存键

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            缓存键字符串
        """
        return self._cache.make_key(
            "quotes",
            stock_code,
            start_date.isoformat(),
            end_date.isoformat(),
        )

    async def close(self) -> None:
        """
        关闭资源连接

        清理缓存连接等资源
        """
        if self._cache:
            await self._cache.close()
        logger.info("data_core_closed")
