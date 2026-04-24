"""Tushare 数据源插件

实现 DataSourceInterface 接口，提供 A 股市场数据获取功能。
"""

import asyncio
from datetime import date, datetime
from typing import Any

import pandas as pd

from app.utils.logger import get_logger
from config import settings
from framework.interfaces.data_source import DataSourceInterface
from framework.models.quote import StandardQuote

from .client import TushareClient
from .exceptions import TushareError, TushareNoDataError
from .mapper import TushareQuoteMapper

logger = get_logger(__name__)


class TusharePlugin:
    """
    Tushare 数据源插件

    实现 DataSourceInterface 协议，提供：
    - A 股日线行情数据获取
    - 实时行情（需 Pro 权限）
    - 健康检查
    - 股票列表获取

    支持市场：SH（上交所）、SZ（深交所）
    """

    # 插件名称
    name: str = "tushare"

    # 插件优先级（数值越小优先级越高）
    priority: int = 10

    # 支持的市场
    supported_markets: list[str] = ["SH", "SZ"]

    # 支持的货币
    supported_currencies: list[str] = ["CNY"]

    def __init__(
        self,
        token: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ):
        """
        初始化 Tushare 插件

        Args:
            token: Tushare API Token（可选，默认从配置读取）
            timeout: 请求超时时间（秒，可选）
            max_retries: 最大重试次数（可选）
        """
        self._client = TushareClient(
            token=token,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._mapper = TushareQuoteMapper()

        logger.info(
            "tushare_plugin_initialized",
            name=self.name,
            supported_markets=self.supported_markets,
        )

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
        # 标准化股票代码
        normalized_code = self._normalize_stock_code(stock_code)

        logger.info(
            "tushare_plugin_get_quotes",
            stock_code=normalized_code,
            start_date=start_date,
            end_date=end_date,
        )

        try:
            # 获取日线数据
            df = await self._client.get_daily_quotes(
                ts_code=normalized_code,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
            )

            # 转换为标准格式
            quotes = self._mapper.map_to_quotes(df, source=self.name)

            if not quotes:
                raise TushareNoDataError(
                    f"未找到股票 {normalized_code} 在 {start_date} 至 {end_date} 的数据"
                )

            logger.info(
                "tushare_plugin_get_quotes_success",
                stock_code=normalized_code,
                quotes_count=len(quotes),
            )

            return quotes

        except TushareError as e:
            logger.error(
                "tushare_plugin_get_quotes_failed",
                stock_code=normalized_code,
                error=str(e),
                error_code=e.code,
            )
            raise

    async def get_realtime_quote(
        self,
        stock_code: str,
    ) -> StandardQuote | None:
        """
        获取实时行情数据

        注意：Tushare 免费版不支持实时行情，需要 Pro 权限。

        Args:
            stock_code: 股票代码

        Returns:
            标准行情数据（单条），如果不支持则返回 None
        """
        normalized_code = self._normalize_stock_code(stock_code)

        logger.debug(
            "tushare_plugin_get_realtime_quote",
            stock_code=normalized_code,
        )

        try:
            # 尝试获取实时数据
            df = await self._client.get_realtime_quote(normalized_code)

            if df is None or df.empty:
                logger.info(
                    "tushare_plugin_realtime_not_supported",
                    stock_code=normalized_code,
                    message="实时行情需要 Tushare Pro 权限",
                )
                return None

            # 转换为标准格式（返回第一条）
            quotes = self._mapper.map_to_quotes(df, source=self.name)
            return quotes[0] if quotes else None

        except Exception as e:
            logger.warning(
                "tushare_plugin_realtime_failed",
                stock_code=normalized_code,
                error=str(e),
            )
            return None

    async def health_check(self) -> bool:
        """
        健康检查

        通过调用 trade_cal 接口验证 Token 是否有效。

        Returns:
            True 如果数据源可用，False 否则
        """
        logger.debug("tushare_plugin_health_check")

        try:
            is_healthy = await self._client.health_check()

            logger.info(
                "tushare_plugin_health_check_result",
                is_healthy=is_healthy,
            )

            return is_healthy

        except Exception as e:
            logger.error(
                "tushare_plugin_health_check_failed",
                error=str(e),
            )
            return False

    async def get_supported_stocks(self, market: str) -> list[str]:
        """
        获取市场支持的股票列表

        Args:
            market: 市场代码（SH 或 SZ）

        Returns:
            股票代码列表（如 ['600519.SH', '000001.SZ']）

        Raises:
            ValueError: 市场代码无效
        """
        # 验证市场代码
        market = market.upper()
        if market not in self.supported_markets:
            logger.warning(
                "tushare_plugin_invalid_market",
                market=market,
                supported_markets=self.supported_markets,
            )
            raise ValueError(
                f"不支持的市场代码：{market}，支持的市场：{self.supported_markets}"
            )

        logger.info(
            "tushare_plugin_get_supported_stocks",
            market=market,
        )

        try:
            # 获取股票列表
            # exchange: SSE=上交所, SZSE=深交所
            exchange = "SSE" if market == "SH" else "SZSE"
            df = await self._client.get_stock_basic(exchange=exchange)

            # 提取股票代码
            stock_codes: list[str] = (
                df["ts_code"].tolist() if "ts_code" in df.columns else []
            )

            logger.info(
                "tushare_plugin_get_supported_stocks_success",
                market=market,
                stocks_count=len(stock_codes),
            )

            return stock_codes

        except Exception as e:
            logger.error(
                "tushare_plugin_get_supported_stocks_failed",
                market=market,
                error=str(e),
            )
            raise

    def _normalize_stock_code(self, code: str) -> str:
        """
        标准化股票代码

        Args:
            code: 原始股票代码

        Returns:
            标准化后的代码（如 '600519.SH'）
        """
        # 转大写
        code = code.upper().strip()

        # 如果没有后缀，根据代码规则推断
        if "." not in code:
            # 上交所：60xxxx（主板）、68xxxx（科创板）
            if code.startswith(("60", "68")):
                code = f"{code}.SH"
            # 深交所：00xxxx（主板）、30xxxx（创业板）
            elif code.startswith(("00", "30")):
                code = f"{code}.SZ"

        return code

    async def close(self) -> None:
        """关闭插件（清理资源）"""
        await self._client.close()
        logger.info("tushare_plugin_closed")

    async def fetch_financial(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """获取每日财务指标（PE/PB/换手率等）

        Args:
            symbol: 股票代码（如 '600519.SH'）
            **kwargs: 额外参数（如 fields, limit 等）

        Returns:
            财务指标 DataFrame
        """
        normalized_code = self._normalize_stock_code(symbol)

        logger.info(
            "tushare_plugin_fetch_financial",
            stock_code=normalized_code,
        )

        try:
            # 透传 kwargs 给底层 client，让业务层控制参数
            df = await self._client.get_daily_basic(
                ts_code=normalized_code,
                **kwargs,
            )

            if df is None or df.empty:
                raise TushareNoDataError(f"未找到股票 {normalized_code} 的财务指标数据")

            logger.info(
                "tushare_plugin_fetch_financial_success",
                stock_code=normalized_code,
                rows=len(df),
            )

            return df

        except TushareError as e:
            logger.error(
                "tushare_plugin_fetch_financial_failed",
                stock_code=normalized_code,
                error=str(e),
            )
            raise

    async def fetch_income(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """获取利润表数据（营收、净利润等）

        Args:
            symbol: 股票代码（如 '600519.SH'）
            **kwargs: 额外参数（如 fields, limit 等）

        Returns:
            利润表 DataFrame
        """
        normalized_code = self._normalize_stock_code(symbol)

        logger.info(
            "tushare_plugin_fetch_income",
            stock_code=normalized_code,
        )

        try:
            # 透传 kwargs 给底层 client，让业务层控制参数
            df = await self._client.get_income(
                ts_code=normalized_code,
                **kwargs,
            )

            if df is None or df.empty:
                raise TushareNoDataError(f"未找到股票 {normalized_code} 的利润表数据")

            logger.info(
                "tushare_plugin_fetch_income_success",
                stock_code=normalized_code,
                rows=len(df),
            )

            return df

        except TushareError as e:
            logger.error(
                "tushare_plugin_fetch_income_failed",
                stock_code=normalized_code,
                error=str(e),
            )
            raise

    async def fetch_fina_indicator(
        self,
        symbol: str,
        **kwargs,
    ) -> pd.DataFrame:
        """获取财务指标数据（ROE/ROA等）

        Args:
            symbol: 股票代码（如 '600519.SH'）
            **kwargs: 额外参数（如 fields, limit 等）

        Returns:
            财务指标 DataFrame
        """
        normalized_code = self._normalize_stock_code(symbol)

        logger.info(
            "tushare_plugin_fetch_fina_indicator",
            stock_code=normalized_code,
        )

        try:
            # 透传 kwargs 给底层 client，让业务层控制参数
            df = await self._client.get_fina_indicator(
                ts_code=normalized_code,
                **kwargs,
            )

            if df is None or df.empty:
                raise TushareNoDataError(f"未找到股票 {normalized_code} 的财务指标数据")

            logger.info(
                "tushare_plugin_fetch_fina_indicator_success",
                stock_code=normalized_code,
                rows=len(df),
            )

            return df

        except TushareError as e:
            logger.error(
                "tushare_plugin_fetch_fina_indicator_failed",
                stock_code=normalized_code,
                error=str(e),
            )
            raise


# 插件注册信息（用于动态加载）
PLUGIN_INFO = {
    "name": "tushare",
    "version": "1.0.0",
    "description": "A 股专业数据源插件，提供深度财务数据、机构持仓等",
    "supported_markets": ["SH", "SZ"],
    "author": "Stock Analyzer Team",
    "dependencies": ["tushare>=1.2.0"],
}
