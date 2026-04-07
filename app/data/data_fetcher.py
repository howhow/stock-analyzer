"""
数据获取协调器

协调多个数据源，实现降级和熔断策略
"""

from datetime import date
from typing import Any

from app.core.cache import CacheManager
from app.core.circuit_breaker import CircuitBreakerRegistry
from app.data.akshare_client import AKShareClient
from app.data.base import BaseDataSource, DataSourceError
from app.data.health_check import HealthChecker, HealthStatus
from app.data.preprocessor import DataPreprocessor
from app.data.tushare_client import TushareClient
from app.models.stock import DailyQuote, FinancialData, IntradayQuote, StockInfo
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class DataFetcher:
    """
    数据获取协调器

    职责：
    1. 管理多个数据源（Tushare主、AKShare备）
    2. 实现降级策略（主数据源失败切换到备用）
    3. 集成熔断器保护
    4. 多级缓存提升性能
    """

    def __init__(
        self,
        tushare_client: TushareClient | None = None,
        akshare_client: AKShareClient | None = None,
        cache: CacheManager | None = None,
    ):
        """
        初始化数据获取协调器

        Args:
            tushare_client: Tushare客户端
            akshare_client: AKShare客户端
            cache: 缓存管理器
        """
        # 数据源客户端
        self.tushare = tushare_client or TushareClient()
        self.akshare = akshare_client or AKShareClient()

        # 缓存
        self.cache = cache or CacheManager()

        # 健康检查器
        self.health_checker = HealthChecker()

        # 数据源优先级
        self.sources: list[BaseDataSource] = [self.tushare, self.akshare]

        # 熔断器注册表
        self.circuit_registry = CircuitBreakerRegistry()

    async def get_stock_info(self, stock_code: str) -> StockInfo:
        """
        获取股票基本信息

        Args:
            stock_code: 股票代码

        Returns:
            股票信息
        """
        cache_key = self.cache.make_key("stock_info", stock_code)

        # 1. 检查缓存
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug("cache_hit", key=cache_key)
            return StockInfo(**cached)

        # 2. 从数据源获取
        errors = []
        for source in self.sources:
            try:
                info = await source.get_stock_info(stock_code)

                # 写入缓存（失败不影响返回）
                try:
                    await self.cache.set(
                        cache_key,
                        info.model_dump(),
                        ttl=settings.cache_ttl_financial,
                    )
                except Exception as e:
                    logger.warning("cache_set_failed", key=cache_key, error=str(e))

                logger.info(
                    "stock_info_fetched",
                    source=source.name,
                    stock_code=stock_code,
                )

                return info

            except Exception as e:
                errors.append((source.name, str(e)))
                logger.warning(
                    "data_source_failed",
                    source=source.name,
                    stock_code=stock_code,
                    error=str(e),
                )
                continue

        # 所有数据源都失败
        raise DataSourceError(
            f"All data sources failed for stock_info: {stock_code}. "
            f"Errors: {errors}"
        )

    async def get_daily_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
        use_cache: bool = True,
    ) -> list[DailyQuote]:
        """
        获取日线行情数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            日线行情列表
        """
        cache_key = self.cache.make_key(
            "daily_quotes",
            stock_code,
            str(start_date),
            str(end_date),
        )

        # 1. 检查缓存
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug("cache_hit", key=cache_key)
                return [DailyQuote(**q) for q in cached]

        # 2. 从数据源获取
        errors = []
        quotes = []

        for source in self.sources:
            try:
                quotes = await source.get_daily_quotes(stock_code, start_date, end_date)

                if quotes:
                    # 数据预处理
                    quotes = DataPreprocessor.clean_daily_quotes(quotes)

                    # 写入缓存
                    if use_cache:
                        await self.cache.set(
                            cache_key,
                            [q.model_dump() for q in quotes],
                            ttl=settings.cache_ttl_daily,
                        )

                    logger.info(
                        "daily_quotes_fetched",
                        source=source.name,
                        stock_code=stock_code,
                        count=len(quotes),
                    )

                    return quotes

            except Exception as e:
                errors.append((source.name, str(e)))
                logger.warning(
                    "data_source_failed",
                    source=source.name,
                    stock_code=stock_code,
                    error=str(e),
                )
                continue

        # 所有数据源都失败
        if not quotes:
            raise DataSourceError(
                f"All data sources failed for daily_quotes: {stock_code}. "
                f"Errors: {errors}"
            )

        return quotes

    async def get_intraday_quotes(
        self,
        stock_code: str,
    ) -> list[IntradayQuote]:
        """
        获取分钟线行情数据

        Args:
            stock_code: 股票代码

        Returns:
            分钟线行情列表
        """
        cache_key = self.cache.make_key("intraday_quotes", stock_code)

        # 1. 检查缓存
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug("cache_hit", key=cache_key)
            return [IntradayQuote(**q) for q in cached]

        # 2. 从数据源获取
        quotes = []

        for source in self.sources:
            try:
                quotes = await source.get_intraday_quotes(stock_code)

                if quotes:
                    # 写入缓存（分钟线缓存时间较短）
                    await self.cache.set(
                        cache_key,
                        [q.model_dump() for q in quotes],
                        ttl=settings.cache_ttl_realtime,
                    )

                    logger.info(
                        "intraday_quotes_fetched",
                        source=source.name,
                        stock_code=stock_code,
                        count=len(quotes),
                    )

                    return quotes

            except Exception as e:
                logger.warning(
                    "data_source_failed",
                    source=source.name,
                    stock_code=stock_code,
                    error=str(e),
                )
                continue

        # 分钟线数据可能不支持，返回空列表而不是抛异常
        logger.info(
            "intraday_quotes_not_available",
            stock_code=stock_code,
        )
        return []

    async def get_financial_data(
        self,
        stock_code: str,
    ) -> FinancialData | None:
        """
        获取财务数据

        Args:
            stock_code: 股票代码

        Returns:
            财务数据
        """
        cache_key = self.cache.make_key("financial_data", stock_code)

        # 1. 检查缓存
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug("cache_hit", key=cache_key)
            return FinancialData(**cached)

        # 2. 从数据源获取
        for source in self.sources:
            try:
                data = await source.get_financial_data(stock_code)

                if data:
                    # 写入缓存
                    await self.cache.set(
                        cache_key,
                        data.model_dump(),
                        ttl=settings.cache_ttl_financial,
                    )

                    logger.info(
                        "financial_data_fetched",
                        source=source.name,
                        stock_code=stock_code,
                    )

                    return data

            except Exception as e:
                logger.warning(
                    "data_source_failed",
                    source=source.name,
                    stock_code=stock_code,
                    error=str(e),
                )
                continue

        # 财务数据可能不存在，返回None
        return None

    async def health_check(self) -> dict[str, HealthStatus]:
        """
        健康检查所有数据源

        Returns:
            数据源名称 -> 健康状态
        """
        return await self.health_checker.check_all(self.sources, force=True)

    async def get_circuit_breaker_status(self) -> dict[str, dict[str, Any]]:
        """
        获取熔断器状态

        Returns:
            熔断器状态信息
        """
        return self.circuit_registry.get_all_status()

    async def reset_circuit_breakers(self) -> None:
        """重置所有熔断器"""
        self.circuit_registry.reset_all()
        logger.info("circuit_breakers_reset")

    async def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        return await self.cache.get_stats()

    async def close(self) -> None:
        """关闭所有连接"""
        await self.tushare.close()
        await self.cache.close()
