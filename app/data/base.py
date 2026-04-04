"""
数据源基类

定义数据源接口抽象和通用方法
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Protocol

from app.models.stock import DailyQuote, FinancialData, IntradayQuote, StockInfo


class DataSourceError(Exception):
    """数据源错误"""

    pass


class DataSourceProtocol(Protocol):
    """
    数据源协议

    定义数据源必须实现的方法
    """

    async def get_stock_info(self, stock_code: str) -> StockInfo:
        """获取股票基本信息"""
        ...

    async def get_daily_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[DailyQuote]:
        """获取日线行情"""
        ...

    async def get_intraday_quotes(
        self,
        stock_code: str,
    ) -> list[IntradayQuote]:
        """获取分钟线行情"""
        ...

    async def get_financial_data(
        self,
        stock_code: str,
    ) -> FinancialData | None:
        """获取财务数据"""
        ...

    async def health_check(self) -> bool:
        """健康检查"""
        ...


class BaseDataSource(ABC):
    """
    数据源基类

    提供通用方法和接口定义
    """

    def __init__(self, name: str, timeout: int = 10):
        """
        初始化数据源

        Args:
            name: 数据源名称
            timeout: 请求超时时间（秒）
        """
        self.name = name
        self.timeout = timeout

    @abstractmethod
    async def get_stock_info(self, stock_code: str) -> StockInfo:
        """
        获取股票基本信息

        Args:
            stock_code: 股票代码（如 600519.SH）

        Returns:
            股票基本信息
        """
        pass

    @abstractmethod
    async def get_daily_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[DailyQuote]:
        """
        获取日线行情数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            日线行情列表
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_financial_data(
        self,
        stock_code: str,
    ) -> FinancialData | None:
        """
        获取财务数据

        Args:
            stock_code: 股票代码

        Returns:
            财务数据，如果不存在返回None
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True: 健康
            False: 不健康
        """
        pass

    def _normalize_stock_code(self, code: str) -> str:
        """
        标准化股票代码

        Args:
            code: 原始股票代码

        Returns:
            标准化后的代码（如 600519.SH）
        """
        # 转大写
        code = code.upper().strip()

        # 如果没有后缀，根据代码规则推断
        if "." not in code:
            if code.startswith(("60", "68")):
                code = f"{code}.SH"
            elif code.startswith(("00", "30")):
                code = f"{code}.SZ"
            elif code.startswith(("007", "009", "01")):
                code = f"{code}.HK"

        return code

    def _extract_market(self, stock_code: str) -> str:
        """
        从股票代码提取市场

        Args:
            stock_code: 标准化的股票代码

        Returns:
            市场代码（SH/SZ/HK）
        """
        parts = stock_code.split(".")
        return parts[1] if len(parts) == 2 else "UNKNOWN"
