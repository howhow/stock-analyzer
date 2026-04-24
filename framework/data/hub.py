"""数据源管理器 — 统一接口 + 自动降级 + 熔断保护

设计原则:
- 主源失败自动降级到备用源
- 熔断器保护，避免雪崩
- EventBus 事件通知
- async 原生支持
- DRY: 公共降级逻辑抽取到 _fetch_with_fallback

使用方式:
    hub = DataHub(sources=[tushare_source, akshare_source])
    df = await hub.fetch_daily("600519.SH")
"""

from typing import Optional

import pandas as pd

from framework.events import Events

from .circuit_breaker import CircuitBreaker


class NoDataSourceAvailable(Exception):
    """所有数据源均不可用"""


class DataHub:
    """数据源管理器 — 统一接口 + 自动降级 + 熔断保护

    Args:
        sources: 数据源插件列表（按优先级排序，index 0 为最高优先级）
        breaker: 熔断器实例（默认使用默认参数创建）
    """

    def __init__(
        self,
        sources: list,
        breaker: Optional[CircuitBreaker] = None,
    ):
        # 按优先级排序（priority 越小优先级越高）
        self._sources = sorted(sources, key=lambda s: s.priority)
        self._breaker = breaker or CircuitBreaker()

    @property
    def breaker(self) -> CircuitBreaker:
        """暴露熔断器实例（供外部检查状态）"""
        return self._breaker

    async def fetch_daily(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取日线数据 — 主源失败自动降级到备用源

        Args:
            symbol: 股票代码（如 "600519.SH"）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            日线数据 DataFrame

        Raises:
            NoDataSourceAvailable: 所有数据源均不可用
        """
        return await self._fetch_with_fallback(
            symbol,
            "fetch_daily",
            start_date=start_date,
            end_date=end_date,
            **kwargs,
        )

    async def fetch_financial(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """获取财务数据 — 主源失败自动降级

        Args:
            symbol: 股票代码

        Returns:
            财务数据 DataFrame

        Raises:
            NoDataSourceAvailable: 所有数据源均不可用
        """
        return await self._fetch_with_fallback(symbol, "fetch_financial", **kwargs)

    async def fetch_income(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """获取利润表数据 — 主源失败自动降级

        Args:
            symbol: 股票代码

        Returns:
            利润表 DataFrame

        Raises:
            NoDataSourceAvailable: 所有数据源均不可用
        """
        return await self._fetch_with_fallback(symbol, "fetch_income", **kwargs)

    async def fetch_fina_indicator(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """获取财务指标数据 — 主源失败自动降级

        Args:
            symbol: 股票代码

        Returns:
            财务指标 DataFrame

        Raises:
            NoDataSourceAvailable: 所有数据源均不可用
        """
        return await self._fetch_with_fallback(symbol, "fetch_fina_indicator", **kwargs)

    async def _fetch_with_fallback(
        self,
        symbol: str,
        fetch_method: str,
        **kwargs,
    ) -> pd.DataFrame:
        """通用降级获取逻辑

        遍历所有数据源（按优先级排序）：
        1. 检查熔断器状态（should_retry）
        2. 尝试获取数据
        3. 成功：record_success + 返回数据
        4. 失败：record_failure + 尝试下一个源
        5. 所有源失败：抛出 NoDataSourceAvailable

        Args:
            symbol: 股票代码
            fetch_method: 数据源方法名（如 "fetch_daily", "fetch_financial"）

        Returns:
            数据 DataFrame

        Raises:
            NoDataSourceAvailable: 所有数据源均不可用
        """
        last_error: Optional[Exception] = None

        for source in self._sources:
            source_name = source.name

            if not self._breaker.should_retry(source_name):
                continue

            try:
                fetch_fn = getattr(source, fetch_method)
                df = await fetch_fn(symbol, **kwargs)
                self._breaker.record_success(source_name)

                Events.data_fetched.send(
                    self,
                    source=source_name,
                    symbol=symbol,
                )

                return df

            except Exception as e:
                last_error = e
                self._breaker.record_failure(source_name)

                Events.data_source_failed.send(
                    self,
                    source=source_name,
                    error=str(e),
                )

        raise NoDataSourceAvailable(
            f"All sources failed for {fetch_method} of {symbol}"
            + (f": {last_error}" if last_error else "")
        )

    def get_source_status(self) -> dict:
        """获取所有数据源的状态

        Returns:
            {source_name: {state, failure_count, priority}}
        """
        status = {}
        for source in self._sources:
            name = source.name
            status[name] = {
                "state": self._breaker.get_state(name).value,
                "failure_count": self._breaker.get_failure_count(name),
                "priority": source.priority,
            }
        return status
