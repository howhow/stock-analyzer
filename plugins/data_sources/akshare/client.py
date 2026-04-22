"""
AKShare API 客户端

封装 AKShare 库的常用接口，提供异步调用支持
"""

import asyncio
import logging
from datetime import date
from typing import Any

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)


class AKShareClientError(Exception):
    """AKShare 客户端错误"""

    pass


class AKShareClient:
    """
    AKShare API 客户端

    封装 AKShare 接口调用，支持：
    - 历史行情数据获取
    - 实时行情数据获取
    - 股票列表获取
    """

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
    ):
        """
        初始化客户端

        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._available = True

    async def get_history_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "daily",
        adjust: str = "qfq",
    ) -> pd.DataFrame | None:
        """
        获取历史行情数据

        Args:
            symbol: 股票代码（纯数字，如 '600519'）
            start_date: 开始日期（格式：'20240101'）
            end_date: 结束日期（格式：'20240131'）
            period: 周期（'daily', 'weekly', 'monthly'）
            adjust: 复权类型（'qfq': 前复权, 'hfq': 后复权, '': 不复权）

        Returns:
            DataFrame 或 None
        """
        return await self._call_api(
            ak.stock_zh_a_hist,
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )

    async def get_realtime_data(self) -> pd.DataFrame | None:
        """
        获取 A 股实时行情数据

        Returns:
            DataFrame 或 None
        """
        return await self._call_api(ak.stock_zh_a_spot_em)

    async def get_stock_list(self, market: str = "A股") -> pd.DataFrame | None:
        """
        获取股票列表

        Args:
            market: 市场类型（'A股', '创业板', '科创板', '北交所'）

        Returns:
            DataFrame 或 None
        """
        try:
            # 使用实时行情数据提取股票列表
            df = await self.get_realtime_data()
            if df is None or df.empty:
                return None

            # 根据市场过滤
            if market == "A股":
                return df
            elif market == "科创板":
                # 科创板代码以 688 开头
                return df[df["代码"].str.startswith("688")]
            elif market == "创业板":
                # 创业板代码以 300 开头
                return df[df["代码"].str.startswith("300")]
            elif market == "北交所":
                # 北交所代码以 8 开头
                return df[df["代码"].str.startswith("8")]

            return df
        except Exception as e:
            logger.error(f"Failed to get stock list: {e}")
            return None

    async def check_availability(self) -> bool:
        """
        检查 AKShare 服务是否可用

        Returns:
            True 如果可用
        """
        try:
            df = await self.get_realtime_data()
            return df is not None and not df.empty
        except Exception:
            return False

    async def _call_api(self, func: Any, **kwargs: Any) -> pd.DataFrame | None:
        """
        调用 AKShare API（带重试）

        Args:
            func: AKShare 函数
            **kwargs: 函数参数

        Returns:
            DataFrame 或 None
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                # AKShare 是同步 API，放到线程池执行
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: func(**kwargs),
                )
                self._available = True
                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"AKShare API call failed"
                    f" (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                # 等待后重试
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)

        self._available = False
        logger.error(
            f"AKShare API call failed after {self.max_retries} retries: {last_error}"
        )
        return None

    @property
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self._available

    @staticmethod
    def normalize_stock_code(stock_code: str) -> tuple[str, str]:
        """
        标准化股票代码

        Args:
            stock_code: 股票代码（如 '600519.SH' 或 '600519'）

        Returns:
            (纯代码, 市场) 元组
        """
        if "." in stock_code:
            code, market = stock_code.split(".")
            return code, market

        # 根据代码规则推断市场
        if stock_code.startswith("6"):
            return stock_code, "SH"
        elif stock_code.startswith(("0", "3")):
            return stock_code, "SZ"
        elif stock_code.startswith("688"):
            return stock_code, "SH"
        elif stock_code.startswith("8"):
            return stock_code, "BJ"
        else:
            return stock_code, "UNKNOWN"
