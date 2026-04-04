"""
数据预处理单元测试
"""

from datetime import date, timedelta

import pytest

from app.data.preprocessor import DataPreprocessor
from app.models.stock import DailyQuote


class TestDataPreprocessor:
    """数据预处理器测试"""

    def test_clean_daily_quotes_valid(self):
        """测试清洗有效的日线数据"""
        quotes = [
            DailyQuote(
                stock_code="600519.SH",
                trade_date=date(2026, 4, 1),
                open=1800.0,
                close=1820.0,
                high=1830.0,
                low=1790.0,
                volume=50000,
                amount=90000000,
            ),
        ]

        cleaned = DataPreprocessor.clean_daily_quotes(quotes)
        assert len(cleaned) == 1

    def test_clean_daily_quotes_invalid_price(self):
        """测试过滤无效价格"""
        # Pydantic模型会自动验证，无法创建open=0的模型
        # 这里测试过滤异常涨跌幅
        quotes = [
            DailyQuote(
                stock_code="600519.SH",
                trade_date=date(2026, 4, 1),
                open=100.0,
                close=200.0,  # 涨幅100%，异常
                high=200.0,
                low=100.0,
                volume=50000,
                amount=90000000,
            ),
        ]

        cleaned = DataPreprocessor.clean_daily_quotes(quotes)
        assert len(cleaned) == 0  # 异常数据被过滤

    def test_clean_daily_quotes_abnormal_change(self):
        """测试过滤异常涨跌幅"""
        quotes = [
            DailyQuote(
                stock_code="600519.SH",
                trade_date=date(2026, 4, 1),
                open=100.0,
                close=200.0,  # 涨幅100%，异常
                high=200.0,
                low=100.0,
                volume=50000,
                amount=90000000,
            ),
        ]

        cleaned = DataPreprocessor.clean_daily_quotes(quotes)
        assert len(cleaned) == 0

    def test_normalize_volume_large(self):
        """测试标准化大成交量"""
        volume = 5_000_000_000  # 50亿，可能是股数
        normalized = DataPreprocessor.normalize_volume(volume)
        assert normalized == 50_000_000  # 转换为手

    def test_normalize_volume_small(self):
        """测试标准化小成交量"""
        volume = 50000  # 已经是手
        normalized = DataPreprocessor.normalize_volume(volume)
        assert normalized == 50000

    def test_validate_data_integrity_empty(self):
        """测试验证空数据"""
        result = DataPreprocessor.validate_data_integrity([])
        assert result["valid"] is False
        assert result["reason"] == "No data"

    def test_validate_data_integrity_valid(self):
        """测试验证有效数据"""
        today = date.today()
        quotes = [
            DailyQuote(
                stock_code="600519.SH",
                trade_date=today - timedelta(days=i),
                open=1800.0,
                close=1820.0,
                high=1830.0,
                low=1790.0,
                volume=50000,
                amount=90000000,
            )
            for i in range(5)
        ]

        result = DataPreprocessor.validate_data_integrity(quotes)
        assert result["valid"] is True
        assert result["actual_days"] == 5

    def test_validate_data_integrity_insufficient(self):
        """测试验证数据不足"""
        today = date.today()
        quotes = [
            DailyQuote(
                stock_code="600519.SH",
                trade_date=today - timedelta(days=i),
                open=1800.0,
                close=1820.0,
                high=1830.0,
                low=1790.0,
                volume=50000,
                amount=90000000,
            )
            for i in range(5)
        ]

        result = DataPreprocessor.validate_data_integrity(
            quotes, expected_days=100
        )
        # 5 < 100 * 0.9
        assert result["valid"] is False
        assert result["reason"] == "Insufficient data"
