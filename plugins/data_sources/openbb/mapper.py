"""
OpenBB 数据转换器

将 OpenBB 返回数据转换为 StandardQuote 格式。
"""

from datetime import date, datetime
from typing import Any, cast, Literal

from framework.models.quote import StandardQuote


class OpenBBMapper:
    """OpenBB 数据到 StandardQuote 的转换器"""

    # OpenBB 字段到 StandardQuote 字段的映射
    FIELD_MAPPING = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "vwap": None,  # OpenBB 有 VWAP，StandardQuote 没有
        "adj_close": "adj_close",
        "adj_high": None,
        "adj_low": None,
        "adj_open": None,
        "adj_volume": None,
    }

    # 市场货币映射
    MARKET_CURRENCY = {
        "SH": "CNY",  # 上海交易所
        "SZ": "CNY",  # 深圳交易所
        "HK": "HKD",  # 香港交易所
        "US": "USD",  # 美国市场
    }

    @staticmethod
    def convert_stock_code_to_openbb(code: str) -> str:
        """
        将标准股票代码转换为 OpenBB 格式

        标准格式: 600519.SH, 000001.SZ, 0700.HK, AAPL.US
        OpenBB 格式: 600519.SS, 000001.SZ, 0700.HK, AAPL

        Args:
            code: 标准股票代码

        Returns:
            OpenBB 格式的股票代码
        """
        if "." not in code:
            return code

        symbol, market = code.rsplit(".", 1)

        # A股市场：SH 需要转换为 SS
        if market == "SH":
            return f"{symbol}.SS"
        # 深圳市场：SZ 保持不变
        elif market == "SZ":
            return code
        # 港股市场：HK 保持不变
        elif market == "HK":
            return code
        # 美国市场：US 后缀需要去掉
        elif market == "US":
            return symbol
        else:
            # 其他市场保持原样
            return code

    @staticmethod
    def convert_stock_code_from_openbb(
        openbb_code: str, original_market: str = ""
    ) -> str:
        """
        将 OpenBB 格式转换回标准格式

        Args:
            openbb_code: OpenBB 格式的代码
            original_market: 原始市场代码（可选）

        Returns:
            标准股票代码
        """
        if "." not in openbb_code:
            # 无后缀，可能是美股
            if original_market == "US":
                return f"{openbb_code}.US"
            return openbb_code

        symbol, suffix = openbb_code.rsplit(".", 1)

        # SS 转换回 SH
        if suffix == "SS":
            return f"{symbol}.SH"
        # SZ 保持不变
        elif suffix == "SZ":
            return openbb_code
        # HK 保持不变
        elif suffix == "HK":
            return openbb_code
        else:
            return openbb_code

    @staticmethod
    def extract_market_from_code(code: str) -> str:
        """
        从股票代码提取市场代码

        Args:
            code: 股票代码

        Returns:
            市场代码
        """
        if "." in code:
            return code.rsplit(".", 1)[1]
        return "US"  # 默认美股

    @classmethod
    def map_to_standard_quote(
        cls,
        openbb_data: dict[str, Any],
        original_code: str,
    ) -> StandardQuote:
        """
        将 OpenBB 数据映射为 StandardQuote

        Args:
            openbb_data: OpenBB 返回的单条数据
            original_code: 原始股票代码（标准格式）

        Returns:
            StandardQuote 实例
        """
        market = cls.extract_market_from_code(original_code)
        currency_str = cls.MARKET_CURRENCY.get(market, "USD")
        currency = cast(Literal["CNY", "USD", "HKD"], currency_str)

        # 解析日期
        trade_date = openbb_data.get("date")
        if isinstance(trade_date, str):
            trade_date = datetime.strptime(trade_date, "%Y-%m-%d").date()
        elif isinstance(trade_date, datetime):
            trade_date = trade_date.date()

        # 计算数据完整度
        completeness = cls._calculate_completeness(openbb_data)

        # 计算质量评分
        quality_score = cls._calculate_quality_score(openbb_data)

        return StandardQuote(
            code=original_code,
            trade_date=trade_date or date.today(),
            open=openbb_data.get("open"),
            high=openbb_data.get("high"),
            low=openbb_data.get("low"),
            close=openbb_data.get("close", 0.0),
            adj_close=openbb_data.get("adj_close"),
            volume=openbb_data.get("volume"),
            amount=openbb_data.get("amount"),
            turnover_rate=openbb_data.get("turnover_rate"),
            source="openbb",
            completeness=completeness,
            quality_score=quality_score,
            currency=currency,
        )

    @classmethod
    def map_to_standard_quotes(
        cls,
        openbb_results: list[dict[str, Any]],
        original_code: str,
    ) -> list[StandardQuote]:
        """
        批量转换 OpenBB 数据

        Args:
            openbb_results: OpenBB 返回的数据列表
            original_code: 原始股票代码

        Returns:
            StandardQuote 列表
        """
        quotes = []
        for data in openbb_results:
            try:
                quote = cls.map_to_standard_quote(data, original_code)
                quotes.append(quote)
            except Exception:
                # 跳过无效数据，继续处理
                continue
        return quotes

    @staticmethod
    def _calculate_completeness(data: dict[str, Any]) -> float:
        """
        计算数据完整度

        Args:
            data: 数据字典

        Returns:
            完整度评分 (0-1)
        """
        # 关键字段
        required_fields = ["date", "close"]
        important_fields = ["open", "high", "low", "volume"]
        optional_fields = ["adj_close", "amount", "turnover_rate"]

        score = 0.0
        total_weight = 0.0

        # 必填字段权重 0.4
        for field in required_fields:
            total_weight += 0.2
            if field in data and data[field] is not None:
                score += 0.2

        # 重要字段权重 0.4
        for field in important_fields:
            total_weight += 0.1
            if field in data and data[field] is not None:
                score += 0.1

        # 可选字段权重 0.2
        for field in optional_fields:
            total_weight += 0.067
            if field in data and data[field] is not None:
                score += 0.067

        return min(score / total_weight, 1.0) if total_weight > 0 else 0.0

    @staticmethod
    def _calculate_quality_score(data: dict[str, Any]) -> float:
        """
        计算数据质量评分

        Args:
            data: 数据字典

        Returns:
            质量评分 (0-1)
        """
        score = 1.0

        # 检查价格逻辑
        open_price = data.get("open")
        high_price = data.get("high")
        low_price = data.get("low")
        close_price = data.get("close")

        if all(p is not None for p in [open_price, high_price, low_price, close_price]):
            # 最高价 >= 最低价
            if high_price is not None and low_price is not None:
                if high_price < low_price:
                    score -= 0.3

            # 收盘价在最高价和最低价之间
            if (
                low_price is not None
                and close_price is not None
                and high_price is not None
            ):
                if not (low_price <= close_price <= high_price):
                    score -= 0.2

            # 开盘价在最高价和最低价之间
            if (
                low_price is not None
                and open_price is not None
                and high_price is not None
            ):
                if not (low_price <= open_price <= high_price):
                    score -= 0.1

        # 检查成交量为正数
        volume = data.get("volume")
        if volume is not None and volume < 0:
            score -= 0.2

        return max(0.0, min(1.0, score))
