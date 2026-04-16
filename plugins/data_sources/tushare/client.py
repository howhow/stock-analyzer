"""Tushare API 客户端

封装 Tushare Pro API 调用，支持异步、熔断、重试等特性。
"""

import asyncio
from datetime import date, datetime
from typing import Any

import pandas as pd
import tushare as ts

from app.core.circuit_breaker import CircuitBreaker
from app.utils.logger import get_logger
from config import settings
from .exceptions import (
    TushareAuthError,
    TushareCircuitBreakerError,
    TushareError,
    TushareNoDataError,
    TushareRateLimitError,
    TushareTimeoutError,
)

logger = get_logger(__name__)


class TushareClient:
    """
    Tushare API 客户端

    封装 Tushare Pro API 调用，提供：
    - 异步接口
    - 熔断保护
    - 自动重试
    - 速率限制处理
    """

    def __init__(
        self,
        token: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ):
        """
        初始化 Tushare 客户端

        Args:
            token: Tushare API Token（可选，默认从配置读取）
            timeout: 请求超时时间（秒，可选）
            max_retries: 最大重试次数（可选）
        """
        self.token = token or settings.tushare_token
        self.timeout = timeout or settings.tushare_timeout
        self.max_retries = max_retries or settings.tushare_max_retries

        # 初始化 Tushare Pro API
        self._pro: Any = None
        if self.token:
            ts.set_token(self.token)  # type: ignore

        # 熔断器
        self._circuit_breaker = CircuitBreaker(
            name="tushare_plugin",
            failure_threshold=settings.circuit_breaker_threshold,
            timeout_seconds=settings.circuit_breaker_timeout,
        )

        # 速率限制状态
        self._last_call_time: float = 0.0
        self._min_interval: float = 0.1  # 最小调用间隔 100ms

        logger.info(
            "tushare_client_initialized",
            has_token=bool(self.token),
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    @property
    def pro(self) -> Any:
        """
        获取 Tushare Pro API 实例

        Returns:
            Tushare Pro API 实例

        Raises:
            TushareAuthError: Token 未配置
        """
        if not self._pro:
            if not self.token:
                raise TushareAuthError("Tushare token 未配置，请设置 TUSHARE_TOKEN 环境变量")
            self._pro = ts.pro_api()  # type: ignore
        return self._pro

    async def get_daily_quotes(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        获取日线行情数据

        Args:
            ts_code: 股票代码（如 '600519.SH'）
            start_date: 开始日期（格式：YYYYMMDD）
            end_date: 结束日期（格式：YYYYMMDD）

        Returns:
            日线行情 DataFrame

        Raises:
            TushareAuthError: 认证失败
            TushareRateLimitError: 速率限制
            TushareTimeoutError: 请求超时
            TushareNoDataError: 无数据
        """
        result = await self._call_api(
            self.pro.daily,
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )
        
        if result is None or result.empty:
            raise TushareNoDataError(f"未找到股票 {ts_code} 在 {start_date} 至 {end_date} 的数据")
        
        return result

    async def get_realtime_quote(self, ts_code: str) -> pd.DataFrame | None:
        """
        获取实时行情数据

        注意：Tushare 免费版不支持实时行情，需要 Pro 权限

        Args:
            ts_code: 股票代码

        Returns:
            实时行情 DataFrame（如果支持），否则返回 None
        """
        try:
            # 尝试调用 realtime 接口
            result = await self._call_api(
                self.pro.realtime_quote,
                ts_code=ts_code,
            )
            return result
        except Exception as e:
            logger.warning(
                "tushare_realtime_not_supported",
                ts_code=ts_code,
                error=str(e),
            )
            return None

    async def get_stock_basic(self, exchange: str = "", list_status: str = "L") -> pd.DataFrame:
        """
        获取股票基础信息列表

        Args:
            exchange: 交易所代码（SSE 上交所，SZSE 深交所，空字符串表示全部）
            list_status: 上市状态（L 上市，D 退市，P 暂停上市）

        Returns:
            股票基础信息 DataFrame

        Raises:
            TushareAuthError: 认证失败
            TushareRateLimitError: 速率限制
        """
        result = await self._call_api(
            self.pro.stock_basic,
            exchange=exchange,
            list_status=list_status,
            fields="ts_code,symbol,name,area,industry,market,list_date",
        )
        
        if result is None or result.empty:
            raise TushareNoDataError("未找到股票列表数据")
        
        return result

    async def get_trade_calendar(
        self,
        exchange: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        获取交易日历

        Args:
            exchange: 交易所代码（SSE/SZSE）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）

        Returns:
            交易日历 DataFrame
        """
        result = await self._call_api(
            self.pro.trade_cal,
            exchange=exchange,
            start_date=start_date,
            end_date=end_date,
        )
        
        return result if result is not None else pd.DataFrame()

    async def health_check(self) -> bool:
        """
        健康检查

        通过调用 trade_cal 接口验证 Token 是否有效

        Returns:
            True: 健康
            False: 不健康
        """
        try:
            today = datetime.now().strftime("%Y%m%d")
            result = await self._call_api(
                self.pro.trade_cal,
                exchange="SSE",
                start_date=today,
                end_date=today,
            )
            return result is not None and not result.empty
        except Exception as e:
            logger.error("tushare_health_check_failed", error=str(e))
            return False

    async def _call_api(self, func: Any, **kwargs: Any) -> pd.DataFrame | None:
        """
        调用 Tushare API（带熔断、重试、速率限制）

        Args:
            func: Tushare API 函数
            **kwargs: API 参数

        Returns:
            API 返回的 DataFrame

        Raises:
            TushareAuthError: 认证失败
            TushareRateLimitError: 速率限制
            TushareTimeoutError: 请求超时
            TushareCircuitBreakerError: 熔断器开启
        """
        # 检查熔断器
        if not await self._circuit_breaker.can_execute():
            raise TushareCircuitBreakerError(
                f"Tushare 服务熔断中，请稍后重试（状态：{self._circuit_breaker.state}）"
            )

        # 速率限制
        await self._rate_limit()

        # 重试逻辑
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                # Tushare 是同步 API，放到线程池执行
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: func(**kwargs),
                )

                # 记录成功
                await self._circuit_breaker.record_success()
                logger.debug(
                    "tushare_api_success",
                    func=func.__name__,
                    attempt=attempt + 1,
                )
                
                return result

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                logger.warning(
                    "tushare_api_retry",
                    func=func.__name__,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                )

                # 认证错误 - 不重试
                if "token" in error_msg or "auth" in error_msg:
                    await self._circuit_breaker.record_failure()
                    raise TushareAuthError(f"Tushare 认证失败：{e}") from e

                # 速率限制 - 等待后重试
                if "rate" in error_msg or "limit" in error_msg:
                    retry_after = 60  # 默认等待 60 秒
                    if attempt < self.max_retries - 1:
                        logger.info(
                            "tushare_rate_limit_retry",
                            retry_after=retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        raise TushareRateLimitError(retry_after=retry_after) from e

                # 超时错误 - 等待后重试
                if "timeout" in error_msg:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise TushareTimeoutError() from e

                # 其他错误 - 等待后重试
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        # 所有重试失败
        await self._circuit_breaker.record_failure()
        raise TushareError(
            f"Tushare API 调用失败（重试 {self.max_retries} 次后）：{last_error}",
            code="API_ERROR",
        )

    async def _rate_limit(self) -> None:
        """
        速率限制控制

        确保两次 API 调用之间有最小间隔
        """
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self._last_call_time
        
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        
        self._last_call_time = asyncio.get_event_loop().time()

    async def close(self) -> None:
        """关闭客户端（清理资源）"""
        logger.info("tushare_client_closed")
