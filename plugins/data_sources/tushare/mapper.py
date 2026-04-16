"""Tushare 数据转换器

将 Tushare API 返回的数据转换为 StandardQuote 标准格式。
"""

from datetime import date, datetime
from typing import Any

import pandas as pd

from framework.models.quote import StandardQuote
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TushareQuoteMapper:
    """
    Tushare 数据转换器

    将 Tushare API 返回的 DataFrame 转换为 StandardQuote 列表。
    负责字段映射、类型转换、数据质量评估。
    """

    # 字段映射：Tushare 字段 -> StandardQuote 字段
    FIELD_MAPPING = {
        "ts_code": "code",
        "trade_date": "trade_date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "pre_close": "pre_close",
        "change": "change",
        "pct_chg": "pct_chg",
        "vol": "volume",
        "amount": "amount",
    }

    # 必须字段（用于计算完整度）
    REQUIRED_FIELDS = ["code", "trade_date", "close"]

    # 价格字段（用于完整度计算）
    PRICE_FIELDS = ["open", "high", "low", "close"]

    # 成交字段（用于完整度计算）
    VOLUME_FIELDS = ["volume", "amount"]

    @classmethod
    def map_to_quotes(
        cls,
        df: pd.DataFrame,
        source: str = "tushare",
    ) -> list[StandardQuote]:
        """
        将 Tushare DataFrame 转换为 StandardQuote 列表

        Args:
            df: Tushare API 返回的 DataFrame
            source: 数据源名称

        Returns:
            StandardQuote 列表

        Raises:
            ValueError: 数据为空或格式错误
        """
        if df is None or df.empty:
            logger.warning("tushare_mapper_empty_data")
            return []

        quotes: list[StandardQuote] = []
        
        for _, row in df.iterrows():
            try:
                quote = cls._map_row_to_quote(row, source)
                if quote:
                    quotes.append(quote)
            except Exception as e:
                logger.error(
                    "tushare_mapper_row_failed",
                    row_data=row.to_dict(),
                    error=str(e),
                )
                continue

        # 按日期升序排序（Tushare 默认返回倒序）
        quotes.sort(key=lambda q: q.trade_date)

        logger.info(
            "tushare_mapper_success",
            total_rows=len(df),
            mapped_quotes=len(quotes),
        )
        
        return quotes

    @classmethod
    def _map_row_to_quote(
        cls,
        row: pd.Series,
        source: str,
    ) -> StandardQuote | None:
        """
        将单行数据转换为 StandardQuote

        Args:
            row: DataFrame 单行数据
            source: 数据源名称

        Returns:
            StandardQuote 实例，如果转换失败返回 None
        """
        # 提取基础字段
        code = cls._extract_string(row, "ts_code")
        trade_date = cls._extract_date(row, "trade_date")
        
        # 必须字段验证
        if not code or not trade_date:
            logger.warning(
                "tushare_mapper_missing_required",
                code=code,
                trade_date=trade_date,
            )
            return None

        # 提取价格字段
        open_price = cls._extract_float(row, "open")
        high_price = cls._extract_float(row, "high")
        low_price = cls._extract_float(row, "low")
        close_price = cls._extract_float(row, "close")

        # close 是必须字段
        if close_price is None:
            logger.warning(
                "tushare_mapper_missing_close",
                code=code,
                trade_date=trade_date,
            )
            return None

        # 提取成交字段
        volume = cls._extract_int(row, "vol")
        amount = cls._extract_float(row, "amount")

        # 计算完整度评分
        completeness = cls._calculate_completeness(
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
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

        # 创建 StandardQuote
        return StandardQuote(
            code=code,
            trade_date=trade_date,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            adj_close=None,  # Tushare daily 接口不提供复权价
            volume=volume,
            amount=amount,
            turnover_rate=None,  # Tushare daily 接口不提供换手率
            source=source,
            completeness=completeness,
            quality_score=quality_score,
            currency="CNY",
        )

    @classmethod
    def _extract_string(cls, row: pd.Series, field: str) -> str | None:
        """提取字符串字段"""
        value = row.get(field)
        if pd.isna(value) or value is None:
            return None
        return str(value).strip()

    @classmethod
    def _extract_float(cls, row: pd.Series, field: str) -> float | None:
        """提取浮点数字段"""
        value = row.get(field)
        if pd.isna(value) or value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _extract_int(cls, row: pd.Series, field: str) -> int | None:
        """提取整数字段"""
        value = row.get(field)
        if pd.isna(value) or value is None:
            return None
        try:
            return int(float(value))  # 先转 float 再转 int
        except (ValueError, TypeError):
            return None

    @classmethod
    def _extract_date(cls, row: pd.Series, field: str) -> date | None:
        """
        提取日期字段

        Tushare 日期格式：YYYYMMDD 或 YYYY-MM-DD
        """
        value = row.get(field)
        if pd.isna(value) or value is None:
            return None
        
        date_str = str(value).strip()
        
        try:
            # YYYYMMDD 格式
            if len(date_str) == 8 and date_str.isdigit():
                return datetime.strptime(date_str, "%Y%m%d").date()
            # YYYY-MM-DD 格式
            elif "-" in date_str:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                logger.warning(
                    "tushare_mapper_invalid_date_format",
                    field=field,
                    value=date_str,
                )
                return None
        except ValueError as e:
            logger.warning(
                "tushare_mapper_parse_date_failed",
                field=field,
                value=date_str,
                error=str(e),
            )
            return None

    @classmethod
    def _calculate_completeness(
        cls,
        open_price: float | None,
        high_price: float | None,
        low_price: float | None,
        close_price: float | None,
        volume: int | None,
        amount: float | None,
    ) -> float:
        """
        计算数据完整度评分

        完整度基于以下字段的存在情况：
        - 价格字段（4个）：open, high, low, close
        - 成交字段（2个）：volume, amount

        Returns:
            完整度评分（0-1）
        """
        # 价格字段权重：60%
        price_score = 0.0
        price_fields = [open_price, high_price, low_price, close_price]
        price_count = sum(1 for f in price_fields if f is not None)
        price_score = (price_count / len(price_fields)) * 0.6

        # 成交字段权重：40%
        volume_score = 0.0
        volume_fields = [volume, amount]
        volume_count = sum(1 for f in volume_fields if f is not None)
        volume_score = (volume_count / len(volume_fields)) * 0.4

        return round(price_score + volume_score, 2)

    @classmethod
    def _calculate_quality_score(
        cls,
        open_price: float | None,
        high_price: float | None,
        low_price: float | None,
        close_price: float | None,
    ) -> float:
        """
        计算数据质量评分

        质量评分基于数据的合理性和逻辑正确性：
        - 价格逻辑检查（最高 >= 最低，收盘价在范围内）
        - 价格有效性（正数、非零）

        Returns:
            质量评分（0-1）
        """
        # 如果缺少必要价格字段，质量评分降低
        if None in [open_price, high_price, low_price, close_price]:
            return 0.5

        # 类型检查器需要明确的类型
        assert open_price is not None
        assert high_price is not None
        assert low_price is not None
        assert close_price is not None

        score = 1.0

        # 检查价格是否为正数
        if any(p <= 0 for p in [open_price, high_price, low_price, close_price]):
            score *= 0.8

        # 检查最高价 >= 最低价
        if high_price < low_price:
            score *= 0.5

        # 检查收盘价在最高价和最低价之间
        if not (low_price <= close_price <= high_price):
            score *= 0.7

        # 检查开盘价在合理范围内（允许一定偏差）
        price_range = high_price - low_price
        if price_range > 0:
            # 开盘价偏离最高/最低价太远
            if open_price < low_price - price_range * 0.1 or open_price > high_price + price_range * 0.1:
                score *= 0.9

        return round(score, 2)
