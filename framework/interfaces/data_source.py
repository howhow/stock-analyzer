"""
数据源接口协议

定义所有数据源插件必须实现的接口。
"""

from datetime import date
from typing import Protocol, runtime_checkable

import pandas as pd

from framework.models.quote import StandardQuote


@runtime_checkable
class DataSourceInterface(Protocol):
    """
    数据源接口协议

    所有数据源插件（Tushare、AKShare、OpenBB等）必须实现此接口。
    使用 Protocol 实现结构化子类型（鸭子类型）。
    """

    @property
    def name(self) -> str:
        """
        数据源名称

        Returns:
            数据源名称（如 'tushare', 'akshare', 'openbb'）
        """
        ...

    @property
    def supported_markets(self) -> list[str]:
        """
        支持的市场

        Returns:
            市场代码列表（如 ['SH', 'SZ', 'HK', 'US']）
        """
        ...

    async def get_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[StandardQuote]:
        """
        获取行情数据

        Args:
            stock_code: 股票代码（如 '600519.SH'）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            标准行情数据列表

        Raises:
            DataSourceError: 数据获取失败
            DataSourceTimeoutError: 数据获取超时
            NoDataError: 无数据
        """
        ...

    async def get_realtime_quote(
        self,
        stock_code: str,
    ) -> StandardQuote | None:
        """
        获取实时行情数据

        Args:
            stock_code: 股票代码

        Returns:
            标准行情数据（单条），如果不支持则返回 None
        """
        ...

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True 如果数据源可用，False 否则
        """
        ...

    async def get_supported_stocks(self, market: str) -> list[str]:
        """
        获取市场支持的股票列表

        Args:
            market: 市场代码

        Returns:
            股票代码列表
        """
        ...

    # ═══════════════════════════════════════════════════════════════
    # 财务数据接口（v1.3 新增）
    # 每个方法只获取一种原始数据，返回 DataFrame
    # 数据聚合由业务层完成
    # ═══════════════════════════════════════════════════════════════

    async def fetch_financial(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """
        获取每日财务指标（PE/PB/换手率等）

        Args:
            symbol: 股票代码（如 '600519.SH'）

        Returns:
            财务指标 DataFrame
        """
        ...

    async def fetch_income(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """
        获取利润表数据（营收、净利润等）

        Args:
            symbol: 股票代码（如 '600519.SH'）

        Returns:
            利润表 DataFrame
        """
        ...

    async def fetch_fina_indicator(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """
        获取财务指标数据（ROE/ROA等）

        Args:
            symbol: 股票代码（如 '600519.SH'）

        Returns:
            财务指标 DataFrame
        """
        ...
