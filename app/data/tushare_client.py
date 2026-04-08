"""
Tushare客户端

实现Tushare数据源接口
"""

import asyncio
from datetime import date, datetime
from typing import Any

import httpx
import tushare as ts

from app.core.circuit_breaker import CircuitBreaker
from app.data.base import BaseDataSource, DataSourceError
from app.data.field_mapper import FieldMapper
from app.models.stock import DailyQuote, FinancialData, IntradayQuote, StockInfo
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class TushareClient(BaseDataSource):
    """
    Tushare数据源客户端

    封装Tushare API调用，支持熔断和超时
    """

    def __init__(
        self,
        token: str = "",
        timeout: int = 10,
        max_retries: int = 3,
    ):
        """
        初始化Tushare客户端

        Args:
            token: Tushare API Token
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        super().__init__(name="tushare", timeout=timeout)
        self.token = token or settings.tushare_token
        self.max_retries = max_retries

        # 初始化Tushare
        if self.token:
            ts.set_token(self.token)
        self.pro = ts.pro_api() if self.token else None

        # 熔断器
        self.circuit_breaker = CircuitBreaker(
            name="tushare",
            failure_threshold=settings.circuit_breaker_threshold,
            timeout_seconds=settings.circuit_breaker_timeout,
        )

        # HTTP客户端（用于健康检查）
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client

    async def get_stock_info(self, stock_code: str) -> StockInfo:
        """
        获取股票基本信息

        Args:
            stock_code: 股票代码（如 600519.SH）

        Returns:
            股票基本信息
        """
        stock_code = self._normalize_stock_code(stock_code)

        if not self.pro:
            raise DataSourceError("Tushare token not configured")

        try:
            # Tushare API调用（同步转异步）
            result = await self._call_tushare(
                self.pro.stock_basic,
                ts_code=stock_code,
                fields="ts_code,name,industry,list_date,market",
            )

            if result is None or len(result) == 0:
                raise DataSourceError(f"Stock not found: {stock_code}")

            data = result.iloc[0].to_dict()
            mapped = FieldMapper.map_tushare(data)

            return StockInfo(
                code=mapped.get("stock_code", stock_code),
                name=mapped.get("name", ""),
                market=mapped.get("market", self._extract_market(stock_code)),
                industry=mapped.get("industry"),
                list_date=self._parse_date(mapped.get("list_date")),
            )

        except Exception as e:
            logger.error(
                "tushare_get_stock_info_failed",
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

        try:
            result = await self._call_tushare(
                self.pro.daily,  # type: ignore[union-attr]
                ts_code=stock_code,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
            )

            if result is None or len(result) == 0:
                return []

            # 转换为列表
            quotes = []
            for _, row in result.iterrows():
                data = FieldMapper.map_tushare(row.to_dict())
                quotes.append(
                    DailyQuote(
                        stock_code=data.get("stock_code", stock_code),
                        trade_date=self._parse_date(data.get("trade_date"))
                        or date.today(),
                        open=float(data.get("open", 0)),
                        close=float(data.get("close", 0)),
                        high=float(data.get("high", 0)),
                        low=float(data.get("low", 0)),
                        volume=float(data.get("volume", 0)),
                        amount=float(data.get("amount", 0)),
                        turnover_rate=data.get("turnover_rate"),
                    )
                )

            # 按日期升序排序（Tushare返回倒序数据）
            quotes.sort(key=lambda q: q.trade_date)

            return quotes

        except Exception as e:
            logger.error(
                "tushare_get_daily_quotes_failed",
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

        注意：Tushare免费版不支持分钟线数据

        Args:
            stock_code: 股票代码

        Returns:
            分钟线行情列表
        """
        # Tushare免费版不支持分钟线，返回空列表
        logger.warning(
            "tushare_intraday_not_supported",
            stock_code=stock_code,
            message="Intraday data requires Tushare Pro subscription",
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
        stock_code = self._normalize_stock_code(stock_code)

        try:
            # 获取最新财务数据
            result = await self._call_tushare(
                self.pro.daily_basic,  # type: ignore[union-attr]
                ts_code=stock_code,
                fields="ts_code,trade_date,pe,pb,turnover_rate",
            )

            if result is None or len(result) == 0:
                return None

            # 获取最新的数据
            data = result.iloc[0].to_dict()
            mapped = FieldMapper.map_tushare(data)

            return FinancialData(
                stock_code=mapped.get("stock_code", stock_code),
                report_date=self._parse_date(mapped.get("trade_date")) or date.today(),
                pe_ratio=mapped.get("pe_ratio"),
                pb_ratio=mapped.get("pb_ratio"),
            )

        except Exception as e:
            logger.error(
                "tushare_get_financial_data_failed",
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
            # 调用trade_calendar接口检查连接
            result = await self._call_tushare(
                self.pro.trade_cal,  # type: ignore[union-attr]
                exchange="SSE",
                start_date=datetime.now().strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
            )
            return result is not None and len(result) > 0
        except Exception as e:
            logger.error("tushare_health_check_failed", error=str(e))
            return False

    async def _call_tushare(self, func: Any, **kwargs: Any) -> Any:
        """
        调用Tushare API（带熔断和重试）

        Args:
            func: Tushare API函数
            **kwargs: API参数

        Returns:
            API返回数据

        Raises:
            DataSourceError: 数据源错误
        """
        if not self.pro:
            raise DataSourceError("Tushare token not configured")

        # 检查熔断器
        if not await self.circuit_breaker.can_execute():
            raise DataSourceError(
                f"Tushare circuit breaker is open: {self.circuit_breaker.state}"
            )

        # 重试逻辑
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                # Tushare是同步API，放到线程池执行
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: func(**kwargs)
                )
                await self.circuit_breaker.record_success()
                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    "tushare_call_retry",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                )

                # 不重试的错误（如认证失败）
                if "token" in str(e).lower() or "auth" in str(e).lower():
                    await self.circuit_breaker.record_failure()
                    raise DataSourceError(f"Tushare auth error: {e}") from e

                # 等待后重试
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)

        # 所有重试失败
        await self.circuit_breaker.record_failure()
        raise DataSourceError(
            f"Tushare call failed after {self.max_retries} retries: {last_error}"
        )

    def _parse_date(self, date_str: str | None) -> date | None:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            # Tushare格式：YYYYMMDD
            if len(date_str) == 8:
                return datetime.strptime(date_str, "%Y%m%d").date()
            # 其他格式
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    async def close(self) -> None:
        """关闭客户端"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
