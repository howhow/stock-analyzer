"""
AKShare客户端

实现AKShare数据源接口（免费数据源）
"""

import asyncio
from datetime import date, datetime
from typing import Any

import akshare as ak
import pandas as pd

from app.core.circuit_breaker import CircuitBreaker
from app.data.base import BaseDataSource, DataSourceError
from app.data.field_mapper import FieldMapper
from app.models.stock import DailyQuote, FinancialData, IntradayQuote, StockInfo
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class AKShareClient(BaseDataSource):
    """
    AKShare数据源客户端

    封装AKShare API调用，支持熔断和超时
    AKShare是免费数据源，无需token
    """

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
    ):
        """
        初始化AKShare客户端

        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        super().__init__(name="akshare", timeout=timeout)
        self.max_retries = max_retries

        # 熔断器
        self.circuit_breaker = CircuitBreaker(
            name="akshare",
            failure_threshold=settings.circuit_breaker_threshold,
            timeout_seconds=settings.circuit_breaker_timeout,
        )

    async def get_stock_info(self, stock_code: str) -> StockInfo:
        """
        获取股票基本信息

        Args:
            stock_code: 股票代码（如 600519.SH）

        Returns:
            股票基本信息
        """
        stock_code = self._normalize_stock_code(stock_code)
        code, market = self._split_code(stock_code)

        try:
            # 获取A股股票信息
            if market in ("SH", "SZ"):
                result = await self._call_akshare(
                    ak.stock_individual_info_em,
                    symbol=code,
                )

                if result is None or result.empty:
                    raise DataSourceError(f"Stock not found: {stock_code}")

                # 解析返回数据
                info_dict = self._parse_individual_info(result)
                mapped = FieldMapper.map_akshare(info_dict)

                return StockInfo(
                    code=stock_code,
                    name=mapped.get("name", ""),
                    market=market,
                    industry=mapped.get("industry"),
                    list_date=self._parse_date(mapped.get("list_date")),
                )

            # 港股暂不支持
            raise DataSourceError(f"HK stocks not supported: {stock_code}")

        except Exception as e:
            logger.error(
                "akshare_get_stock_info_failed",
                stock_code=stock_code,
                error=str(e),
            )
            raise DataSourceError(f"Failed to get stock info: {e}") from e

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
        stock_code = self._normalize_stock_code(stock_code)
        code, market = self._split_code(stock_code)

        try:
            # 获取A股日线数据
            if market == "SH":
                result = await self._call_akshare(
                    ak.stock_zh_a_hist,
                    symbol=code,
                    period="daily",
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                    adjust="qfq",  # 前复权
                )
            elif market == "SZ":
                result = await self._call_akshare(
                    ak.stock_zh_a_hist,
                    symbol=code,
                    period="daily",
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                    adjust="qfq",
                )
            else:
                return []

            if result is None or result.empty:
                return []

            # 转换为列表
            quotes = []
            for _, row in result.iterrows():
                data = FieldMapper.map_akshare(row.to_dict())
                trade_date = self._parse_date(data.get("trade_date"))
                if trade_date is None:
                    continue

                quotes.append(
                    DailyQuote(
                        stock_code=stock_code,
                        trade_date=trade_date,
                        open=float(data.get("open", 0)),
                        close=float(data.get("close", 0)),
                        high=float(data.get("high", 0)),
                        low=float(data.get("low", 0)),
                        volume=float(data.get("volume", 0)),
                        amount=float(data.get("amount", 0)),
                        turnover_rate=data.get("turnover_rate"),
                    )
                )

            return quotes

        except Exception as e:
            logger.error(
                "akshare_get_daily_quotes_failed",
                stock_code=stock_code,
                start_date=str(start_date),
                end_date=str(end_date),
                error=str(e),
            )
            raise DataSourceError(f"Failed to get daily quotes: {e}") from e

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
        stock_code = self._normalize_stock_code(stock_code)
        code, market = self._split_code(stock_code)

        try:
            # 仅支持A股
            if market not in ("SH", "SZ"):
                return []

            result = await self._call_akshare(
                ak.stock_zh_a_minute,
                symbol=code,
                period="1",
                adjust="qfq",
            )

            if result is None or result.empty:
                return []

            # 转换为列表
            quotes = []
            for _, row in result.iterrows():
                data = FieldMapper.map_akshare(row.to_dict())
                trade_time = self._parse_datetime(data.get("trade_date"))
                if trade_time is None:
                    continue

                quotes.append(
                    IntradayQuote(
                        stock_code=stock_code,
                        trade_time=trade_time,
                        open=float(data.get("open", 0)),
                        close=float(data.get("close", 0)),
                        high=float(data.get("high", 0)),
                        low=float(data.get("low", 0)),
                        volume=float(data.get("volume", 0)),
                        amount=float(data.get("amount", 0)),
                    )
                )

            return quotes

        except Exception as e:
            logger.error(
                "akshare_get_intraday_quotes_failed",
                stock_code=stock_code,
                error=str(e),
            )
            # 分钟线失败不抛异常，返回空列表
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
        stock_code = self._normalize_stock_code(stock_code)
        code, market = self._split_code(stock_code)

        try:
            if market not in ("SH", "SZ"):
                return None

            # 获取主要财务指标
            result = await self._call_akshare(
                ak.stock_financial_analysis_indicator,
                symbol=code,
            )

            if result is None or result.empty:
                return None

            # 获取最新数据
            data = result.iloc[0].to_dict()
            mapped = FieldMapper.map_akshare(data)

            report_date = self._parse_date(mapped.get("report_date"))
            if not report_date:
                return None

            return FinancialData(
                stock_code=stock_code,
                report_date=report_date,
                revenue=mapped.get("revenue"),
                net_profit=mapped.get("net_profit"),
                total_assets=mapped.get("total_assets"),
                total_liabilities=mapped.get("total_liabilities"),
                roe=mapped.get("roe"),
                pe_ratio=mapped.get("pe_ratio"),
                pb_ratio=mapped.get("pb_ratio"),
                debt_ratio=mapped.get("debt_ratio"),
            )

        except Exception as e:
            logger.error(
                "akshare_get_financial_data_failed",
                stock_code=stock_code,
                error=str(e),
            )
            return None

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True: 健康
            False: 不健康
        """
        try:
            # 尝试获取实时数据
            result = await self._call_akshare(
                ak.stock_zh_a_spot_em,
            )
            return result is not None and not result.empty
        except Exception as e:
            logger.error("akshare_health_check_failed", error=str(e))
            return False

    async def _call_akshare(self, func: Any, **kwargs: Any) -> pd.DataFrame:
        """
        调用AKShare API（带熔断和重试）

        Args:
            func: AKShare API函数
            **kwargs: API参数

        Returns:
            API返回数据（DataFrame）

        Raises:
            DataSourceError: 数据源错误
        """
        # 检查熔断器
        if not await self.circuit_breaker.can_execute():
            raise DataSourceError(
                f"AKShare circuit breaker is open: {self.circuit_breaker.state}"
            )

        # 重试逻辑
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                # AKShare是同步API，放到线程池执行
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: func(**kwargs)
                )
                await self.circuit_breaker.record_success()
                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    "akshare_call_retry",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                )

                # 网络错误等待后重试
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)

        # 所有重试失败
        await self.circuit_breaker.record_failure()
        raise DataSourceError(
            f"AKShare call failed after {self.max_retries} retries: {last_error}"
        )

    def _split_code(self, stock_code: str) -> tuple[str, str]:
        """
        分离股票代码和市场

        Args:
            stock_code: 标准化股票代码（如 600519.SH）

        Returns:
            (代码, 市场) 元组
        """
        parts = stock_code.split(".")
        if len(parts) == 2:
            return parts[0], parts[1]
        return stock_code, "UNKNOWN"

    def _parse_individual_info(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        解析个股信息

        Args:
            df: AKShare返回的DataFrame

        Returns:
            信息字典
        """
        info: dict[str, Any] = {}
        if df is None or df.empty:
            return info

        # AKShare返回格式是两列：item, value
        for _, row in df.iterrows():
            item = str(row.iloc[0])
            value = row.iloc[1]
            info[item] = value

        return info

    def _parse_date(self, date_str: str | None) -> date | None:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            # 尝试多种格式
            for fmt in ["%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(str(date_str), fmt).date()
                except ValueError:
                    continue
            return None
        except (ValueError, TypeError):
            return None

    def _parse_datetime(self, datetime_str: str | None) -> datetime | None:
        """解析日期时间字符串"""
        if not datetime_str:
            return None
        try:
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y%m%d%H%M%S",
            ]:
                try:
                    return datetime.strptime(str(datetime_str), fmt)
                except ValueError:
                    continue
            return None
        except (ValueError, TypeError):
            return None
