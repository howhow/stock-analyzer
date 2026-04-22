"""
数据转换器

将 DataFrame 转换为 StandardQuote 对象。
"""

from datetime import date
from typing import Literal

import pandas as pd

from framework.models.quote import StandardQuote


class QuoteMapper:
    """
    行情数据转换器

    将 DataFrame 行转换为 StandardQuote 对象。
    支持多种字段命名风格。
    """

    # 字段映射表：DataFrame 列名 -> StandardQuote 字段
    FIELD_MAPPING = {
        # 日期字段
        "date": "trade_date",
        "Date": "trade_date",
        # 价格字段
        "open": "open",
        "Open": "open",
        "high": "high",
        "High": "high",
        "low": "low",
        "Low": "low",
        "close": "close",
        "Close": "close",
        "adj_close": "adj_close",
        "Adj Close": "adj_close",
        "adjclose": "adj_close",
        # 成交字段
        "volume": "volume",
        "Volume": "volume",
        "amount": "amount",
        "Amount": "amount",
        "turnover_rate": "turnover_rate",
    }

    def __init__(self, source_name: str = "local"):
        """
        初始化转换器

        Args:
            source_name: 数据源名称
        """
        self.source_name = source_name

    def map_row(
        self,
        row: pd.Series,
        stock_code: str,
        currency: Literal["CNY", "USD", "HKD"] = "CNY",
    ) -> StandardQuote:
        """
        将 DataFrame 行转换为 StandardQuote

        Args:
            row: DataFrame 的一行
            stock_code: 股票代码
            currency: 货币类型

        Returns:
            StandardQuote 对象
        """
        # 提取日期
        trade_date = self._extract_date(row)

        # 提取价格数据
        open_price = self._safe_float(row.get("open"))
        high_price = self._safe_float(row.get("high"))
        low_price = self._safe_float(row.get("low"))
        close_price_raw = self._safe_float(row.get("close"))
        adj_close = self._safe_float(row.get("adj_close"))

        # close 不能为 None
        close_price = close_price_raw if close_price_raw is not None else 0.0

        # 提取成交数据
        volume = self._safe_int(row.get("volume"))
        amount = self._safe_float(row.get("amount"))
        turnover_rate = self._safe_float(row.get("turnover_rate"))

        # 计算数据质量评分
        completeness, quality_score = self._calculate_quality(
            open_price, high_price, low_price, close_price, volume
        )

        return StandardQuote(
            code=stock_code,
            trade_date=trade_date,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            adj_close=adj_close,
            volume=volume,
            amount=amount,
            turnover_rate=turnover_rate,
            source=self.source_name,
            completeness=completeness,
            quality_score=quality_score,
            currency=currency,
        )

    def map_dataframe(
        self,
        df: pd.DataFrame,
        stock_code: str,
        currency: Literal["CNY", "USD", "HKD"] = "CNY",
    ) -> list[StandardQuote]:
        """
        将整个 DataFrame 转换为 StandardQuote 列表

        Args:
            df: 行情数据 DataFrame
            stock_code: 股票代码
            currency: 货币类型

        Returns:
            StandardQuote 列表
        """
        quotes = []
        for _, row in df.iterrows():
            quote = self.map_row(row, stock_code, currency)
            quotes.append(quote)
        return quotes

    def _extract_date(self, row: pd.Series) -> date:
        """从行中提取日期"""
        date_value = row.get("date") or row.get("trade_date")
        if date_value is None:
            raise ValueError("Missing date field in data row")

        if isinstance(date_value, pd.Timestamp):
            dt: date = date_value.date()
            return dt
        if isinstance(date_value, str):
            parsed = pd.to_datetime(date_value)
            if hasattr(parsed, "date"):
                d: date = parsed.date()
                return d
            return date(parsed.year, parsed.month, parsed.day)
        if isinstance(date_value, date):
            return date_value

        raise ValueError(f"Unsupported date format: {type(date_value)}")

    def _safe_float(self, value) -> float | None:
        """安全转换为 float"""
        if value is None or pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value) -> int | None:
        """安全转换为 int"""
        if value is None or pd.isna(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _calculate_quality(
        self,
        open_price: float | None,
        high_price: float | None,
        low_price: float | None,
        close_price: float | None,
        volume: int | None,
    ) -> tuple[float, float]:
        """
        计算数据完整度和质量评分

        Args:
            open_price, high_price, low_price, close_price, volume: 价格和成交量数据

        Returns:
            (completeness, quality_score) 元组
        """
        # 计算完整度
        fields = [open_price, high_price, low_price, close_price, volume]
        non_null = sum(1 for f in fields if f is not None)
        completeness = non_null / len(fields)

        # 计算质量评分
        quality_score = completeness

        # 如果所有价格都有值，检查价格逻辑
        if all(p is not None for p in [open_price, high_price, low_price, close_price]):
            # 最高价 >= 最低价
            if (
                high_price is not None
                and low_price is not None
                and high_price < low_price
            ):
                quality_score *= 0.5
            # 收盘价在最高价和最低价之间
            elif (
                low_price is not None
                and close_price is not None
                and high_price is not None
                and not (low_price <= close_price <= high_price)
            ):
                quality_score *= 0.7

        return completeness, quality_score
