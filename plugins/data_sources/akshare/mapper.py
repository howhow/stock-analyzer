"""
AKShare 数据转换器

将 AKShare 返回的 DataFrame 转换为 StandardQuote 标准数据模型
"""

from datetime import date, datetime
from typing import Any

import pandas as pd

from framework.models.quote import StandardQuote


class AKShareMapper:
    """
    AKShare 数据转换器

    负责将 AKShare 原始数据转换为标准格式
    """

    # AKShare DataFrame 字段映射
    FIELD_MAP: dict[str, str] = {
        "日期": "trade_date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "换手率": "turnover_rate",
        "代码": "code",
        "股票代码": "code",
    }

    @classmethod
    def dataframe_to_quotes(
        cls,
        df: pd.DataFrame,
        code: str,
        source: str = "akshare",
    ) -> list[StandardQuote]:
        """
        将 DataFrame 转换为 StandardQuote 列表

        Args:
            df: AKShare 返回的 DataFrame
            code: 股票代码（如 '600519.SH'）
            source: 数据源名称

        Returns:
            StandardQuote 列表
        """
        if df is None or df.empty:
            return []

        quotes: list[StandardQuote] = []

        for _, row in df.iterrows():
            try:
                quote = cls._row_to_quote(row, code, source)
                if quote is not None:
                    quotes.append(quote)
            except Exception:
                # 跳过无效行
                continue

        return quotes

    @classmethod
    def _row_to_quote(
        cls,
        row: pd.Series,
        code: str,
        source: str,
    ) -> StandardQuote | None:
        """
        将单行数据转换为 StandardQuote

        Args:
            row: DataFrame 行数据
            code: 股票代码
            source: 数据源名称

        Returns:
            StandardQuote 对象或 None
        """
        # 解析交易日期
        trade_date = cls._parse_date(row.get("日期") or row.get("trade_date"))
        if trade_date is None:
            return None

        # 解析价格字段
        open_price = cls._parse_float(row.get("开盘") or row.get("open"))
        high_price = cls._parse_float(row.get("最高") or row.get("high"))
        low_price = cls._parse_float(row.get("最低") or row.get("low"))
        close_price = cls._parse_float(row.get("收盘") or row.get("close"))

        # 收盘价是必填字段
        if close_price is None:
            return None

        # 解析成交字段
        volume = cls._parse_int(row.get("成交量") or row.get("volume"))
        amount = cls._parse_float(row.get("成交额") or row.get("amount"))
        turnover_rate = cls._parse_float(row.get("换手率") or row.get("turnover_rate"))

        # 计算数据完整度
        completeness = cls._calculate_completeness(
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            volume=volume,
            amount=amount,
        )

        # 计算质量评分
        quality_score = cls._calculate_quality_score(
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
        )

        return StandardQuote(
            code=code,
            trade_date=trade_date,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            adj_close=None,  # AKShare 历史数据已前复权
            volume=volume,
            amount=amount,
            turnover_rate=turnover_rate,
            source=source,
            completeness=completeness,
            quality_score=quality_score,
            currency="CNY",
        )

    @classmethod
    def _parse_date(cls, value: Any) -> date | None:
        """解析日期"""
        if value is None or pd.isna(value):
            return None

        # 如果已经是 date 类型
        if isinstance(value, date):
            return value

        # 如果是 datetime 类型
        if isinstance(value, datetime):
            return value.date()

        # 字符串解析
        date_str = str(value).strip()
        if not date_str:
            return None

        # 尝试多种日期格式
        formats = [
            "%Y-%m-%d",
            "%Y%m%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    @classmethod
    def _parse_float(cls, value: Any) -> float | None:
        """解析浮点数"""
        if value is None or pd.isna(value):
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _parse_int(cls, value: Any) -> int | None:
        """解析整数"""
        if value is None or pd.isna(value):
            return None

        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    @classmethod
    def _calculate_completeness(
        cls,
        open_price: float | None,
        high_price: float | None,
        low_price: float | None,
        volume: int | None,
        amount: float | None,
    ) -> float:
        """
        计算数据完整度评分

        Args:
            open_price: 开盘价
            high_price: 最高价
            low_price: 最低价
            volume: 成交量
            amount: 成交额

        Returns:
            完整度评分（0-1）
        """
        # 必要字段：开盘、最高、最低
        required_fields = [open_price, high_price, low_price]
        required_count = sum(1 for f in required_fields if f is not None)
        required_score = required_count / len(required_fields)

        # 可选字段：成交量、成交额
        optional_fields = [volume, amount]
        optional_count = sum(1 for f in optional_fields if f is not None)
        optional_score = optional_count / len(optional_fields)

        # 加权评分：必要字段 70%，可选字段 30%
        return required_score * 0.7 + optional_score * 0.3

    @classmethod
    def _calculate_quality_score(
        cls,
        open_price: float | None,
        high_price: float | None,
        low_price: float | None,
        close_price: float,
    ) -> float:
        """
        计算数据质量评分

        Args:
            open_price: 开盘价
            high_price: 最高价
            low_price: 最低价
            close_price: 收盘价

        Returns:
            质量评分（0-1）
        """
        score = 1.0

        # 检查价格逻辑
        if high_price is not None and low_price is not None:
            # 最高价应该 >= 最低价
            if high_price < low_price:
                score *= 0.7  # 严重错误，扣分

        # 检查收盘价是否在合理范围内
        if high_price is not None and low_price is not None:
            if not (low_price <= close_price <= high_price):
                score *= 0.8  # 轻微错误，扣分

        # 检查价格是否为正数
        if close_price <= 0:
            score *= 0.5

        return max(0.0, min(1.0, score))

    @classmethod
    def map_realtime_data(
        cls,
        df: pd.DataFrame,
        code: str,
        source: str = "akshare",
    ) -> StandardQuote | None:
        """
        将实时数据转换为 StandardQuote

        Args:
            df: AKShare 实时数据 DataFrame
            code: 股票代码
            source: 数据源名称

        Returns:
            StandardQuote 对象或 None
        """
        if df is None or df.empty:
            return None

        # 过滤指定股票
        code_num = code.split(".")[0]  # 提取纯代码
        stock_data = df[df["代码"] == code_num]

        if stock_data.empty:
            return None

        # 取第一条数据
        row = stock_data.iloc[0]

        # 实时数据字段映射
        trade_date = date.today()
        open_price = cls._parse_float(row.get("今开"))
        high_price = cls._parse_float(row.get("最高"))
        low_price = cls._parse_float(row.get("最低"))
        close_price = cls._parse_float(row.get("最新价"))

        if close_price is None:
            return None

        volume = cls._parse_int(row.get("成交量"))
        amount = cls._parse_float(row.get("成交额"))

        completeness = cls._calculate_completeness(
            open_price, high_price, low_price, volume, amount
        )

        quality_score = cls._calculate_quality_score(
            open_price, high_price, low_price, close_price
        )

        return StandardQuote(
            code=code,
            trade_date=trade_date,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            adj_close=None,
            volume=volume,
            amount=amount,
            turnover_rate=None,
            source=source,
            completeness=completeness,
            quality_score=quality_score,
            currency="CNY",
        )
