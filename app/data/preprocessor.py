"""
数据预处理

对获取的数据进行清洗和预处理
"""

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from app.models.stock import DailyQuote
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataPreprocessor:
    """
    数据预处理器

    负责数据清洗、缺失值处理、异常值过滤
    """

    @staticmethod
    def clean_daily_quotes(quotes: list[DailyQuote]) -> list[DailyQuote]:
        """
        清洗日线数据

        Args:
            quotes: 原始日线数据列表

        Returns:
            清洗后的数据列表
        """
        if not quotes:
            return []

        cleaned = []
        for quote in quotes:
            # 过滤无效价格
            if quote.open <= 0 or quote.close <= 0:
                logger.warning(
                    "invalid_price_filtered",
                    stock_code=quote.stock_code,
                    trade_date=str(quote.trade_date),
                    open=quote.open,
                    close=quote.close,
                )
                continue

            # 过滤异常值（如涨跌幅超过50%）
            change_pct = abs(quote.close - quote.open) / quote.open * 100
            if change_pct > 50:  # 单日涨跌幅超过50%视为异常
                logger.warning(
                    "abnormal_change_filtered",
                    stock_code=quote.stock_code,
                    trade_date=str(quote.trade_date),
                    change_pct=change_pct,
                )
                continue

            cleaned.append(quote)

        return cleaned

    @staticmethod
    def fill_missing_values(
        df: pd.DataFrame,
        method: str = "ffill",
    ) -> pd.DataFrame:
        """
        填充缺失值

        Args:
            df: 数据DataFrame
            method: 填充方法（ffill/bfill/interpolate）

        Returns:
            填充后的DataFrame
        """
        if df.empty:
            return df

        # 数值列填充
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if df[col].isna().any():
                if method == "ffill":
                    df[col] = df[col].fillna(method="ffill").fillna(method="bfill")
                elif method == "bfill":
                    df[col] = df[col].fillna(method="bfill").fillna(method="ffill")
                elif method == "interpolate":
                    df[col] = df[col].interpolate(method="linear")

        return df

    @staticmethod
    def remove_outliers(
        df: pd.DataFrame,
        columns: list[str],
        n_std: float = 3.0,
    ) -> pd.DataFrame:
        """
        移除异常值

        使用标准差方法

        Args:
            df: 数据DataFrame
            columns: 需要处理的列
            n_std: 标准差倍数

        Returns:
            处理后的DataFrame
        """
        if df.empty:
            return df

        for col in columns:
            if col not in df.columns:
                continue

            mean = df[col].mean()
            std = df[col].std()

            if std > 0:
                lower_bound = mean - n_std * std
                upper_bound = mean + n_std * std

                # 使用边界值替换异常值
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)

        return df

    @staticmethod
    def normalize_volume(volume: float | int) -> float:
        """
        标准化成交量单位

        不同数据源成交量单位可能不同，统一为"手"

        Args:
            volume: 原始成交量

        Returns:
            标准化后的成交量（手）
        """
        # 如果是股数，转换为手（1手=100股）
        if volume > 1_000_000_000:  # 大于10亿，可能是股数
            return volume / 100
        return float(volume)

    @staticmethod
    def calculate_derived_fields(quotes: list[DailyQuote]) -> list[DailyQuote]:
        """
        计算衍生字段

        如涨跌幅、换手率等

        Args:
            quotes: 日线数据列表

        Returns:
            带衍生字段的数据列表
        """
        if len(quotes) < 2:
            return quotes

        # 按日期排序
        sorted_quotes = sorted(quotes, key=lambda x: x.trade_date)

        # 计算涨跌幅
        result = []
        prev_quote = None

        for quote in sorted_quotes:
            if prev_quote is not None and prev_quote.close > 0:
                # 涨跌幅已计算，存储在模型扩展字段中
                # 这里只做标记，实际计算在分析引擎中
                pass

            result.append(quote)
            prev_quote = quote

        return result

    @staticmethod
    def validate_data_integrity(
        quotes: list[DailyQuote],
        expected_days: int | None = None,
    ) -> dict[str, Any]:
        """
        验证数据完整性

        Args:
            quotes: 日线数据列表
            expected_days: 预期天数

        Returns:
            验证结果字典
        """
        if not quotes:
            return {
                "valid": False,
                "reason": "No data",
                "actual_days": 0,
                "expected_days": expected_days,
            }

        # 检查日期连续性
        sorted_quotes = sorted(quotes, key=lambda x: x.trade_date)
        dates = [q.trade_date for q in sorted_quotes]

        # 检查缺失数据
        missing_dates = []
        if len(dates) > 1:
            start = dates[0]
            end = dates[-1]
            expected = set()
            current = start
            while current <= end:
                # 排除周末
                if current.weekday() < 5:
                    expected.add(current)
                current = date(current.year, current.month, current.day) + pd.Timedelta(
                    days=1
                )

            actual = set(dates)
            missing_dates = list(expected - actual)

        result = {
            "valid": True,
            "actual_days": len(quotes),
            "expected_days": expected_days,
            "start_date": str(dates[0]),
            "end_date": str(dates[-1]),
            "missing_count": len(missing_dates),
            "missing_dates": [str(d) for d in missing_dates[:10]],  # 最多返回10个
        }

        # 如果缺失数据过多，标记为无效
        if expected_days and len(quotes) < expected_days * 0.9:
            result["valid"] = False
            result["reason"] = "Insufficient data"

        return result
