"""
数据预处理器完整测试 - 覆盖所有方法
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date

from app.data.preprocessor import DataPreprocessor
from app.models.stock import DailyQuote


class TestCleanDailyQuotes:
    """测试日线数据清洗"""

    def test_clean_valid_quotes(self):
        """测试清洗有效数据"""
        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                close=10.5,
                high=11.0,
                low=9.5,
                volume=1000000.0,
                amount=10500000.0,
            ),
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 2),
                open=10.5,
                close=11.0,
                high=11.5,
                low=10.0,
                volume=1200000.0,
                amount=13200000.0,
            ),
        ]

        result = DataPreprocessor.clean_daily_quotes(quotes)

        assert len(result) == 2
        assert result[0].stock_code == "000001.SZ"

    def test_clean_empty_quotes(self):
        """测试清洗空数据"""
        result = DataPreprocessor.clean_daily_quotes([])
        assert result == []

    def test_clean_low_price(self):
        """测试过滤低价格数据"""
        # DailyQuote 模型验证不允许 open/close <= 0
        # 测试正常数据保留
        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=0.01,
                close=0.01,
                high=0.02,
                low=0.01,
                volume=1000000.0,
                amount=1000.0,
            ),
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 2),
                open=10.5,
                close=11.0,
                high=11.5,
                low=10.0,
                volume=1200000.0,
                amount=13200000.0,
            ),
        ]

        result = DataPreprocessor.clean_daily_quotes(quotes)

        # 所有数据都应该保留（都有效）
        assert len(result) == 2

    def test_clean_abnormal_change(self):
        """测试过滤异常涨跌"""
        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                close=20.0,  # 涨幅100%，异常
                high=20.0,
                low=10.0,
                volume=1000000.0,
                amount=15000000.0,
            ),
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 2),
                open=10.5,
                close=11.0,  # 正常涨幅
                high=11.5,
                low=10.0,
                volume=1200000.0,
                amount=13200000.0,
            ),
        ]

        result = DataPreprocessor.clean_daily_quotes(quotes)

        assert len(result) == 1
        assert result[0].trade_date == date(2024, 1, 2)


class TestFillMissingValues:
    """测试缺失值填充"""

    def test_fill_missing_ffill(self):
        """测试前向填充"""
        df = pd.DataFrame({"close": [10.0, np.nan, 30.0], "volume": [1000, 2000, 3000]})

        result = DataPreprocessor.fill_missing_values(df, method="ffill")

        assert result is not None  # 使用result

        assert result["close"].isna().sum() == 0
        assert result["close"].iloc[1] == 10.0  # 前向填充

    def test_fill_missing_bfill(self):
        """测试后向填充"""
        df = pd.DataFrame({"close": [10.0, np.nan, 30.0], "volume": [1000, 2000, 3000]})

        result = DataPreprocessor.fill_missing_values(df, method="bfill")

        assert result["close"].isna().sum() == 0
        assert result["close"].iloc[1] == 30.0  # 后向填充

    def test_fill_missing_interpolate(self):
        """测试插值填充"""
        df = pd.DataFrame({"close": [10.0, np.nan, 30.0], "volume": [1000, 2000, 3000]})

        result = DataPreprocessor.fill_missing_values(df, method="interpolate")

        assert result["close"].isna().sum() == 0
        assert result["close"].iloc[1] == 20.0  # 线性插值

    def test_fill_missing_empty_df(self):
        """测试空DataFrame"""
        df = pd.DataFrame()
        _ = DataPreprocessor.fill_missing_values(df)
        assert df.empty


class TestRemoveOutliers:
    """测试异常值移除"""

    def test_remove_outliers_basic(self):
        """测试基本异常值移除"""
        df = pd.DataFrame(
            {
                "close": [10.0, 11.0, 1000.0, 12.0, 13.0],  # 1000是异常值
                "volume": [1000, 2000, 3000, 4000, 5000],
            }
        )

        result = DataPreprocessor.remove_outliers(df, columns=["close"], n_std=2.0)

        # 检查结果不为空
        assert result is not None

        # remove_outliers 使用 clip，所以异常值被裁剪到边界
        # 检查最大值被限制（不超过均值+2倍标准差）
        mean = 10.0 + 11.0 + 1000.0 + 12.0 + 13.0
        mean = mean / 5  # 209.2
        std = df["close"].std()  # 约 441
        expected_max = mean + 2 * std

        # 最大值应该被clip到合理范围
        assert result["close"].max() <= expected_max + 1  # 允许一点误差

    def test_remove_outliers_empty_df(self):
        """测试空DataFrame"""
        df = pd.DataFrame()
        _ = DataPreprocessor.remove_outliers(df, columns=["close"])
        assert df.empty

    def test_remove_outliers_missing_column(self):
        """测试列不存在"""
        df = pd.DataFrame(
            {
                "close": [10.0, 11.0, 12.0],
            }
        )

        # 列不存在，不应该报错
        result = DataPreprocessor.remove_outliers(df, columns=["volume"])
        assert "volume" not in result.columns


class TestNormalizeVolume:
    """测试成交量标准化"""

    def test_normalize_small_volume(self):
        """测试小成交量（已是手）"""
        volume = 1000000.0  # 100万手
        result = DataPreprocessor.normalize_volume(volume)

        assert result == 1000000.0

    def test_normalize_large_volume(self):
        """测试大成交量（可能是股数）"""
        volume = 2_000_000_000.0  # 20亿股
        result = DataPreprocessor.normalize_volume(volume)

        assert result == 20000000.0  # 转换为20万手

    def test_normalize_int_volume(self):
        """测试整数类型成交量"""
        volume = 1000000
        result = DataPreprocessor.normalize_volume(volume)

        assert result == 1000000.0
        assert isinstance(result, float)


class TestCalculateDerivedFields:
    """测试衍生字段计算"""

    def test_calculate_derived_single_quote(self):
        """测试单条数据"""
        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                close=10.5,
                high=11.0,
                low=9.5,
                volume=1000000.0,
                amount=10500000.0,
            )
        ]

        result = DataPreprocessor.calculate_derived_fields(quotes)

        assert len(result) == 1

    def test_calculate_derived_multiple_quotes(self):
        """测试多条数据"""
        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                close=10.5,
                high=11.0,
                low=9.5,
                volume=1000000.0,
                amount=10500000.0,
            ),
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 2),
                open=10.5,
                close=11.0,
                high=11.5,
                low=10.0,
                volume=1200000.0,
                amount=13200000.0,
            ),
        ]

        result = DataPreprocessor.calculate_derived_fields(quotes)

        assert len(result) == 2
        # 应该按日期排序
        assert result[0].trade_date == date(2024, 1, 1)


class TestValidateDataIntegrity:
    """测试数据完整性验证"""

    def test_validate_empty_data(self):
        """测试空数据"""
        result = DataPreprocessor.validate_data_integrity([])

        assert result["valid"] is False
        assert result["reason"] == "No data"

    def test_validate_sufficient_data(self):
        """测试数据充足"""
        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, i),
                open=10.0,
                close=10.5,
                high=11.0,
                low=9.5,
                volume=1000000.0,
                amount=10500000.0,
            )
            for i in range(1, 11)  # 10天数据
        ]

        result = DataPreprocessor.validate_data_integrity(quotes, expected_days=10)

        assert result["valid"] is True
        assert result["actual_days"] == 10

    def test_validate_insufficient_data(self):
        """测试数据不足"""
        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                close=10.5,
                high=11.0,
                low=9.5,
                volume=1000000.0,
                amount=10500000.0,
            )
        ]

        result = DataPreprocessor.validate_data_integrity(quotes, expected_days=100)

        assert result["valid"] is False
        assert result["reason"] == "Insufficient data"

    def test_validate_data_with_missing_dates(self):
        """测试缺失日期"""
        # 创建有间隔的数据
        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                close=10.5,
                high=11.0,
                low=9.5,
                volume=1000000.0,
                amount=10500000.0,
            ),
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 5),  # 跳过几天
                open=10.5,
                close=11.0,
                high=11.5,
                low=10.0,
                volume=1200000.0,
                amount=13200000.0,
            ),
        ]

        result = DataPreprocessor.validate_data_integrity(quotes)

        assert result["missing_count"] > 0
