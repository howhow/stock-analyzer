"""
OpenBB 数据源插件

实现 DataSourceInterface，提供全球市场行情数据。
"""

from datetime import date
from typing import Any

import pandas as pd

from app.utils.logger import get_logger
from framework.interfaces.data_source import DataSourceInterface
from framework.models.quote import StandardQuote

from .client import (
    OpenBBClient,
    OpenBBClientError,
    OpenBBNoDataError,
    OpenBBTimeoutError,
)
from .mapper import OpenBBMapper

logger = get_logger(__name__)


class OpenBBPlugin:
    """
    OpenBB 数据源插件

    支持 SH、SZ、HK、US 等全球市场。
    注意：A 股市场支持有限，部分股票可能无数据。
    """

    # 数据源名称
    _name = "openbb"

    # 支持的市场
    _supported_markets = ["SH", "SZ", "HK", "US"]

    # 插件优先级（数值越小优先级越高）
    priority = 30

    def __init__(
        self,
        timeout: int = 30,
        **kwargs: Any,
    ):
        """
        初始化 OpenBB 插件

        Args:
            timeout: 请求超时时间（秒）
            **kwargs: 其他配置参数
        """
        self._client = OpenBBClient(timeout=timeout)
        self._mapper = OpenBBMapper()
        logger.info(f"OpenBB 插件初始化完成，超时: {timeout}秒")

    @property
    def name(self) -> str:
        """数据源名称"""
        return self._name

    @property
    def supported_markets(self) -> list[str]:
        """支持的市场列表"""
        return self._supported_markets.copy()

    async def get_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[StandardQuote]:
        """
        获取历史行情数据

        Args:
            stock_code: 股票代码（标准格式，如 600519.SH）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            标准行情数据列表

        Raises:
            DataSourceError: 数据获取失败
            DataSourceTimeoutError: 数据获取超时
            NoDataError: 无数据
        """
        logger.info(f"OpenBB 获取行情: {stock_code}, {start_date} ~ {end_date}")

        # 验证市场支持
        market = OpenBBMapper.extract_market_from_code(stock_code)
        if market not in self._supported_markets:
            raise OpenBBClientError(
                f"不支持的市场: {market}，支持的市场: {self._supported_markets}"
            )

        # 转换股票代码为 OpenBB 格式
        openbb_code = OpenBBMapper.convert_stock_code_to_openbb(stock_code)
        logger.debug(f"股票代码转换: {stock_code} -> {openbb_code}")

        try:
            # 获取历史数据
            raw_data = await self._client.get_historical(
                symbol=openbb_code,
                start_date=start_date,
                end_date=end_date,
            )

            # 转换为标准格式
            quotes = OpenBBMapper.map_to_standard_quotes(raw_data, stock_code)

            logger.info(f"OpenBB 返回 {len(quotes)} 条数据 ({stock_code})")

            return quotes

        except OpenBBTimeoutError as e:
            logger.error(f"OpenBB 请求超时: {e}")
            raise

        except OpenBBNoDataError as e:
            logger.warning(f"OpenBB 无数据: {e}")
            raise

        except OpenBBClientError as e:
            logger.error(f"OpenBB 客户端错误: {e}")
            raise

        except Exception as e:
            logger.exception(f"OpenBB 未知错误: {e}")
            raise OpenBBClientError(f"获取数据失败: {e}") from e

    async def get_realtime_quote(
        self,
        stock_code: str,
    ) -> StandardQuote | None:
        """
        获取实时行情

        Args:
            stock_code: 股票代码（标准格式）

        Returns:
            标准行情数据，如果不支持则返回 None
        """
        logger.info(f"OpenBB 获取实时行情: {stock_code}")

        # 验证市场支持
        market = OpenBBMapper.extract_market_from_code(stock_code)
        if market not in self._supported_markets:
            logger.warning(f"不支持的市场: {market}")
            return None

        # 转换股票代码
        openbb_code = OpenBBMapper.convert_stock_code_to_openbb(stock_code)

        try:
            raw_data = await self._client.get_quote(openbb_code)

            if raw_data is None:
                logger.info(f"OpenBB 不支持实时行情: {stock_code}")
                return None

            # 转换为标准格式
            quote = OpenBBMapper.map_to_standard_quote(raw_data, stock_code)
            logger.info(f"OpenBB 实时行情获取成功: {stock_code}")
            return quote

        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return None

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True 如果数据源可用
        """
        logger.debug("OpenBB 健康检查")

        try:
            is_healthy = await self._client.health_check()
            status = "正常" if is_healthy else "异常"
            logger.info(f"OpenBB 健康检查: {status}")
            return is_healthy

        except Exception as e:
            logger.error(f"OpenBB 健康检查失败: {e}")
            return False

    async def get_supported_stocks(self, market: str) -> list[str]:
        """
        获取市场支持的股票列表

        Args:
            market: 市场代码（SH, SZ, HK, US）

        Returns:
            股票代码列表
        """
        logger.info(f"OpenBB 获取股票列表: {market}")

        if market not in self._supported_markets:
            logger.warning(f"不支持的市场: {market}")
            return []

        # A股市场特殊处理
        if market in ["SH", "SZ"]:
            logger.warning(
                f"OpenBB 对 A股市场（{market}）支持有限，"
                "建议使用 Tushare 或 AKShare 作为主数据源"
            )
            return []

        try:
            stocks = await self._client.search_stocks(market)
            logger.info(f"OpenBB 返回 {len(stocks)} 只股票 ({market})")
            return stocks

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    async def fetch_daily(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取日线数据（DataHub 兼容接口）

        Args:
            symbol: 股票代码（如 '600519.SH'）
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数

        Returns:
            日线数据 DataFrame
        """
        from datetime import timedelta

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=120)

        quotes = await self.get_quotes(symbol, start_date, end_date)

        if not quotes:
            return pd.DataFrame()

        # 转换为 DataFrame
        data = []
        for q in quotes:
            data.append({
                "ts_code": symbol,
                "trade_date": q.trade_date.strftime("%Y%m%d"),
                "open": q.open,
                "high": q.high,
                "low": q.low,
                "close": q.close,
                "volume": q.volume,
            })

        return pd.DataFrame(data)

    async def fetch_financial(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """获取每日财务指标（PE/PB/换手率等）

        Args:
            symbol: 股票代码（如 '600519.SH'）
            **kwargs: 额外参数

        Returns:
            财务指标 DataFrame
        """
        logger.warning(f"OpenBB 插件暂不支持财务指标数据: {symbol}")
        return pd.DataFrame()

    async def fetch_income(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """获取利润表数据（营收、净利润等）

        Args:
            symbol: 股票代码（如 '600519.SH'）
            **kwargs: 额外参数

        Returns:
            利润表 DataFrame
        """
        logger.warning(f"OpenBB 插件暂不支持利润表数据: {symbol}")
        return pd.DataFrame()

    async def fetch_fina_indicator(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """获取财务指标数据（ROE/ROA等）

        Args:
            symbol: 股票代码（如 '600519.SH'）
            **kwargs: 额外参数

        Returns:
            财务指标 DataFrame
        """
        logger.warning(f"OpenBB 插件暂不支持财务指标数据: {symbol}")
        return pd.DataFrame()

    def __repr__(self) -> str:
        return (
            f"OpenBBPlugin("
            f"name={self._name}, "
            f"markets={self._supported_markets}"
            f")"
        )


# 插件注册信息（用于动态加载）
PLUGIN_INFO = {
    "name": "openbb",
    "version": "1.0.0",
    "description": "OpenBB 数据源插件，支持全球市场数据",
    "supported_markets": ["US", "HK", "CN"],
    "author": "Stock Analyzer Team",
    "dependencies": ["openbb>=4.0.0"],
}
