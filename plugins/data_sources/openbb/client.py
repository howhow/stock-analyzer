"""
OpenBB API 客户端

封装 OpenBB SDK 调用，处理速率限制和错误。
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any

from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenBBClientError(Exception):
    """OpenBB 客户端错误基类"""

    pass


class OpenBBTimeoutError(OpenBBClientError):
    """OpenBB 请求超时"""

    pass


class OpenBBRateLimitError(OpenBBClientError):
    """OpenBB 速率限制"""

    pass


class OpenBBNoDataError(OpenBBClientError):
    """OpenBB 无数据"""

    pass


class OpenBBClient:
    """
    OpenBB API 客户端

    封装 OpenBB SDK 调用，提供：
    - 超时控制
    - 速率限制
    - 错误处理
    - 数据缓存
    """

    # 默认超时时间（秒）
    DEFAULT_TIMEOUT = 30

    # 速率限制配置
    RATE_LIMIT_REQUESTS = 10  # 每分钟请求数
    RATE_LIMIT_WINDOW = 60  # 窗口期（秒）

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        enable_cache: bool = True,
    ):
        """
        初始化 OpenBB 客户端

        Args:
            timeout: 请求超时时间（秒）
            enable_cache: 是否启用缓存
        """
        self.timeout = timeout
        self.enable_cache = enable_cache
        self._obb = None
        self._initialized = False
        self._request_times: list[float] = []

    def _ensure_initialized(self) -> None:
        """确保 OpenBB 已初始化"""
        if not self._initialized:
            try:
                from openbb import obb

                self._obb = obb
                self._initialized = True
                logger.info("OpenBB SDK 初始化成功")
            except ImportError as e:
                raise OpenBBClientError(
                    "OpenBB SDK 未安装，请运行: pip install openbb"
                ) from e

    def _check_rate_limit(self) -> None:
        """检查速率限制"""
        import time

        current_time = time.time()

        # 清理过期的请求时间记录
        self._request_times = [
            t for t in self._request_times
            if current_time - t < self.RATE_LIMIT_WINDOW
        ]

        # 如果超过限制，等待
        if len(self._request_times) >= self.RATE_LIMIT_REQUESTS:
            sleep_time = self.RATE_LIMIT_WINDOW - (current_time - self._request_times[0])
            if sleep_time > 0:
                logger.warning(f"达到速率限制，等待 {sleep_time:.1f} 秒")
                time.sleep(sleep_time)

        # 记录本次请求时间
        self._request_times.append(current_time)

    async def _run_with_timeout(
        self,
        coro: Any,
        timeout: int | None = None,
    ) -> Any:
        """
        带超时的异步执行

        Args:
            coro: 协程或可调用对象
            timeout: 超时时间（秒）

        Returns:
            执行结果

        Raises:
            OpenBBTimeoutError: 超时
        """
        timeout = timeout or self.timeout

        try:
            # OpenBB SDK 是同步的，需要在线程池中运行
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, coro),
                timeout=timeout,
            )
            return result
        except asyncio.TimeoutError as e:
            raise OpenBBTimeoutError(
                f"OpenBB 请求超时（{timeout}秒）"
            ) from e

    def _get_historical_sync(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """
        同步获取历史数据（内部方法）

        Args:
            symbol: 股票代码（OpenBB 格式）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            数据列表
        """
        self._ensure_initialized()
        self._check_rate_limit()

        try:
            # 使用 OpenBB SDK 获取历史数据
            result = self._obb.equity.price.historical(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            # 转换为字典列表
            if hasattr(result, "results") and result.results:
                return [
                    {
                        "date": item.date if hasattr(item, "date") else item.get("date"),
                        "open": item.open if hasattr(item, "open") else item.get("open"),
                        "high": item.high if hasattr(item, "high") else item.get("high"),
                        "low": item.low if hasattr(item, "low") else item.get("low"),
                        "close": item.close if hasattr(item, "close") else item.get("close"),
                        "volume": item.volume if hasattr(item, "volume") else item.get("volume"),
                        "adj_close": item.adj_close if hasattr(item, "adj_close") else item.get("adj_close"),
                    }
                    for item in result.results
                ]
            elif hasattr(result, "to_dict"):
                # 如果是 DataFrame 或其他可转换对象
                df = result.to_dict("records") if hasattr(result, "to_dict") else result
                return df if isinstance(df, list) else [df]
            else:
                return []

        except Exception as e:
            logger.error(f"OpenBB 获取历史数据失败: {e}")
            raise OpenBBClientError(f"获取历史数据失败: {e}") from e

    async def get_historical(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        异步获取历史行情数据

        Args:
            symbol: 股票代码（OpenBB 格式）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据列表

        Raises:
            OpenBBTimeoutError: 请求超时
            OpenBBNoDataError: 无数据
            OpenBBClientError: 其他错误
        """
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        logger.debug(f"OpenBB 获取历史数据: {symbol} {start_str} ~ {end_str}")

        data = await self._run_with_timeout(
            lambda: self._get_historical_sync(symbol, start_str, end_str)
        )

        if not data:
            raise OpenBBNoDataError(f"OpenBB 无数据: {symbol} {start_str} ~ {end_str}")

        return data

    def _get_quote_sync(self, symbol: str) -> dict[str, Any] | None:
        """
        同步获取实时行情（内部方法）

        Args:
            symbol: 股票代码（OpenBB 格式）

        Returns:
            行情数据字典
        """
        self._ensure_initialized()
        self._check_rate_limit()

        try:
            # 尝试获取实时行情
            # 注意：OpenBB 的实时行情支持因数据源而异
            result = self._obb.equity.price.quote(symbol)

            if hasattr(result, "results") and result.results:
                item = result.results[0] if isinstance(result.results, list) else result.results
                return {
                    "symbol": symbol,
                    "price": item.price if hasattr(item, "price") else item.get("price"),
                    "open": item.open if hasattr(item, "open") else item.get("open"),
                    "high": item.high if hasattr(item, "high") else item.get("high"),
                    "low": item.low if hasattr(item, "low") else item.get("low"),
                    "close": item.price if hasattr(item, "price") else item.get("price"),
                    "volume": item.volume if hasattr(item, "volume") else item.get("volume"),
                    "date": datetime.now().date(),
                }
            return None

        except Exception as e:
            logger.warning(f"OpenBB 获取实时行情失败: {e}")
            return None

    async def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """
        异步获取实时行情

        Args:
            symbol: 股票代码（OpenBB 格式）

        Returns:
            行情数据字典，如果不支持则返回 None
        """
        return await self._run_with_timeout(
            lambda: self._get_quote_sync(symbol)
        )

    def _search_stocks_sync(self, market: str) -> list[str]:
        """
        同步搜索股票（内部方法）

        Args:
            market: 市场代码

        Returns:
            股票代码列表
        """
        self._ensure_initialized()
        self._check_rate_limit()

        try:
            # OpenBB 搜索功能
            # 注意：不同市场的支持程度不同
            if market == "US":
                result = self._obb.equity.search()
                if hasattr(result, "results"):
                    return [item.symbol for item in result.results if hasattr(item, "symbol")]
            elif market in ["SH", "SZ"]:
                # A股支持有限
                logger.warning(f"OpenBB 对 A股市场（{market}）支持有限")
                return []
            elif market == "HK":
                result = self._obb.equity.search(market="hk")
                if hasattr(result, "results"):
                    return [item.symbol for item in result.results if hasattr(item, "symbol")]

            return []

        except Exception as e:
            logger.error(f"OpenBB 搜索股票失败: {e}")
            return []

    async def search_stocks(self, market: str) -> list[str]:
        """
        异步搜索股票列表

        Args:
            market: 市场代码

        Returns:
            股票代码列表
        """
        return await self._run_with_timeout(
            lambda: self._search_stocks_sync(market)
        )

    def health_check_sync(self) -> bool:
        """
        同步健康检查

        Returns:
            True 如果服务可用
        """
        try:
            self._ensure_initialized()

            # 尝试获取一个已知的股票数据来验证
            # 使用美股 AAPL 作为测试
            result = self._obb.equity.price.historical(
                symbol="AAPL",
                start_date=(datetime.now().date().replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
            )

            return result is not None and (hasattr(result, "results") or result)

        except Exception as e:
            logger.error(f"OpenBB 健康检查失败: {e}")
            return False

    async def health_check(self) -> bool:
        """
        异步健康检查

        Returns:
            True 如果服务可用
        """
        return await self._run_with_timeout(
            self.health_check_sync,
            timeout=10,  # 健康检查使用更短的超时
        )

    def close(self) -> None:
        """关闭客户端，清理资源"""
        self._obb = None
        self._initialized = False
        self._request_times.clear()
        logger.info("OpenBB 客户端已关闭")