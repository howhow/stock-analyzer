"""
Local 本地数据源插件

从本地 CSV/Parquet 文件加载历史数据，用于离线分析和回测。
"""

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import pandas as pd

from app.core.exceptions import DataSourceError, NoDataError
from framework.models.quote import StandardQuote

from .loader import LocalDataLoader
from .mapper import QuoteMapper

logger = logging.getLogger(__name__)


@dataclass
class LocalPluginConfig:
    """Local 插件配置"""

    data_dir: str = "./data/local"
    file_format: Literal["csv", "parquet"] = "csv"


class LocalPlugin:
    """
    Local 本地数据源插件

    支持从本地文件系统加载历史行情数据。
    不支持实时数据。

    Example:
        ```python
        plugin = LocalPlugin(
            LocalPluginConfig(
                data_dir="./data/historical",
                file_format="parquet",
            )
        )

        quotes = await plugin.get_quotes(
            "600519.SH", date(2024, 1, 1), date(2024, 12, 31)
        )
        ```
    """

    def __init__(self, config: LocalPluginConfig | None = None):
        """
        初始化插件

        Args:
            config: 插件配置，默认使用 LocalPluginConfig 默认值
        """
        self._config = config or LocalPluginConfig()
        self._loader = LocalDataLoader(
            data_dir=self._config.data_dir,
            file_format=self._config.file_format,
        )
        self._mapper = QuoteMapper(source_name="local")

    @property
    def name(self) -> str:
        """数据源名称"""
        return "local"

    @property
    def supported_markets(self) -> list[str]:
        """
        支持的市场

        Local 插件支持所有市场，因为数据来源是本地文件。
        """
        return ["SH", "SZ", "HK", "US"]

    async def get_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[StandardQuote]:
        """
        获取历史行情数据

        Args:
            stock_code: 股票代码 (如 '600519.SH')
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            StandardQuote 列表

        Raises:
            NoDataError: 无数据
            DataSourceError: 数据加载失败
        """
        # 根据股票代码推断货币类型
        currency = self._infer_currency(stock_code)

        # 加载数据
        df = self._loader.load_with_date_filter(
            stock_code=stock_code,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        if df is None or df.empty:
            raise NoDataError(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                source="local",
            )

        try:
            # 转换为 StandardQuote 列表
            quotes = self._mapper.map_dataframe(df, stock_code, currency)
            return quotes
        except Exception as e:
            raise DataSourceError(
                f"Failed to map data for {stock_code}",
                details={"stock_code": stock_code, "error": str(e)},
            )

    async def get_realtime_quote(
        self,
        stock_code: str,
    ) -> StandardQuote | None:
        """
        获取实时行情数据

        Local 插件不支持实时数据，始终返回 None。

        Args:
            stock_code: 股票代码

        Returns:
            None (不支持实时数据)
        """
        return None

    async def health_check(self) -> bool:
        """
        健康检查

        检查数据目录是否存在且可访问。

        Returns:
            True 如果数据目录存在，False 否则
        """
        data_dir = Path(self._config.data_dir)
        return data_dir.exists() and data_dir.is_dir()

    async def get_supported_stocks(self, market: str) -> list[str]:
        """
        获取本地已有的股票数据列表

        Args:
            market: 市场代码 (SH/SZ/HK/US)，目前不用于过滤

        Returns:
            本地数据文件中的股票代码列表
        """
        all_stocks = self._loader.list_available_stocks()

        # 可选：根据市场过滤
        if market and market != "all":
            suffix_map = {
                "SH": ".SH",
                "SZ": ".SZ",
                "HK": ".HK",
                "US": ".US",
            }
            suffix = suffix_map.get(market.upper())
            if suffix:
                all_stocks = [s for s in all_stocks if s.endswith(suffix)]

        return all_stocks

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
        logger.warning(f"Local 插件暂不支持财务指标数据: {symbol}")
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
        logger.warning(f"Local 插件暂不支持利润表数据: {symbol}")
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
        logger.warning(f"Local 插件暂不支持财务指标数据: {symbol}")
        return pd.DataFrame()

    def _infer_currency(self, stock_code: str) -> Literal["CNY", "USD", "HKD"]:
        """
        根据股票代码推断货币类型

        Args:
            stock_code: 股票代码

        Returns:
            货币代码
        """
        if stock_code.endswith(".US"):
            return "USD"
        elif stock_code.endswith(".HK"):
            return "HKD"
        else:
            # SH 和 SZ 默认使用 CNY
            return "CNY"
