"""
AKShare 数据源插件

实现 DataSourceInterface 接口，提供 A 股行情数据
"""

import logging
from datetime import date

from framework.models.quote import StandardQuote

from .client import AKShareClient
from .mapper import AKShareMapper

logger = logging.getLogger(__name__)


class AKSharePlugin:
    """
    AKShare 数据源插件

    实现 DataSourceInterface 协议，提供：
    - A 股历史行情数据
    - A 股实时行情数据
    - 健康检查
    - 股票列表获取
    """

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
    ):
        """
        初始化插件

        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self._client = AKShareClient(
            timeout=timeout,
            max_retries=max_retries,
        )

    @property
    def name(self) -> str:
        """数据源名称"""
        return "akshare"

    @property
    def supported_markets(self) -> list[str]:
        """支持的市场列表"""
        return ["SH", "SZ"]

    async def get_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[StandardQuote]:
        """
        获取历史行情数据

        Args:
            stock_code: 股票代码（如 '600519.SH'）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            标准行情数据列表

        Raises:
            DataSourceError: 数据获取失败
        """
        # 标准化股票代码
        code, market = self._client.normalize_stock_code(stock_code)

        # 检查市场支持
        if market not in self.supported_markets:
            logger.warning(f"Market not supported: {market} for stock {stock_code}")
            return []

        # 格式化日期
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        # 获取数据
        df = await self._client.get_history_data(
            symbol=code,
            start_date=start_str,
            end_date=end_str,
        )

        if df is None or df.empty:
            logger.info(
                f"No data found for {stock_code} from {start_date} to {end_date}"
            )
            return []

        # 转换为标准格式
        quotes = AKShareMapper.dataframe_to_quotes(
            df=df,
            code=stock_code,
            source=self.name,
        )

        logger.info(
            f"Retrieved {len(quotes)} quotes for {stock_code} "
            f"from {start_date} to {end_date}"
        )

        return quotes

    async def get_realtime_quote(
        self,
        stock_code: str,
    ) -> StandardQuote | None:
        """
        获取实时行情数据

        Args:
            stock_code: 股票代码（如 '600519.SH'）

        Returns:
            标准行情数据（单条），如果不支持则返回 None
        """
        # 获取实时数据
        df = await self._client.get_realtime_data()

        if df is None or df.empty:
            logger.warning("Failed to get realtime data")
            return None

        # 转换为标准格式
        quote = AKShareMapper.map_realtime_data(
            df=df,
            code=stock_code,
            source=self.name,
        )

        if quote:
            logger.debug(f"Retrieved realtime quote for {stock_code}")
        else:
            logger.warning(f"Stock not found in realtime data: {stock_code}")

        return quote

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True 如果数据源可用
        """
        is_healthy = await self._client.check_availability()

        if is_healthy:
            logger.info("AKShare health check passed")
        else:
            logger.warning("AKShare health check failed")

        return is_healthy

    async def get_supported_stocks(self, market: str) -> list[str]:
        """
        获取市场支持的股票列表

        Args:
            market: 市场代码（'SH' 或 'SZ'）

        Returns:
            股票代码列表（标准格式，如 '600519.SH'）
        """
        # 检查市场支持
        if market not in self.supported_markets:
            logger.warning(f"Market not supported: {market}")
            return []

        # 获取股票列表
        df = await self._client.get_stock_list()

        if df is None or df.empty:
            logger.warning(f"Failed to get stock list for market {market}")
            return []

        # 过滤指定市场的股票
        stocks: list[str] = []

        for _, row in df.iterrows():
            code = str(row.get("代码", "")).strip()
            if not code:
                continue

            # 根据市场规则过滤
            if market == "SH":
                # 上交所：6 开头
                if code.startswith("6"):
                    stocks.append(f"{code}.SH")
            elif market == "SZ":
                # 深交所：0 或 3 开头
                if code.startswith(("0", "3")):
                    stocks.append(f"{code}.SZ")

        logger.info(f"Retrieved {len(stocks)} stocks for market {market}")

        return stocks

    @property
    def client(self) -> AKShareClient:
        """获取底层客户端（用于测试）"""
        return self._client
