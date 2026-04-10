"""
分析基类测试

测试 BaseAnalyzer 的工具方法
"""

from datetime import date

import pytest

from app.analysis.base import BaseAnalyzer
from app.models.stock import DailyQuote


class MockAnalyzer(BaseAnalyzer):
    """用于测试的模拟分析器"""

    async def analyze(self, quotes: list[DailyQuote], **kwargs):
        return {"test": "result"}


def make_quote(
    trade_date: date,
    open_p: float,
    high: float,
    low: float,
    close: float,
    volume: float,
) -> DailyQuote:
    """创建 DailyQuote 的辅助函数"""
    return DailyQuote(
        stock_code="600519.SH",
        trade_date=trade_date,
        open=open_p,
        high=high,
        low=low,
        close=close,
        volume=volume,
        amount=volume * close / 10,  # 简单计算
    )


class TestBaseAnalyzer:
    """测试 BaseAnalyzer"""

    def test_validate_data_sufficient(self):
        """测试数据充足"""
        analyzer = MockAnalyzer(name="test")
        quotes = [
            make_quote(date(2024, 1, i), 100, 105, 95, 102, 1000000)
            for i in range(1, 31)
        ]

        assert analyzer.validate_data(quotes, min_days=20) is True

    def test_validate_data_insufficient(self):
        """测试数据不足"""
        analyzer = MockAnalyzer(name="test")
        quotes = [
            make_quote(date(2024, 1, i), 100, 105, 95, 102, 1000000)
            for i in range(1, 11)
        ]

        assert analyzer.validate_data(quotes, min_days=20) is False

    def test_extract_price_series(self):
        """测试价格序列提取"""
        analyzer = MockAnalyzer(name="test")
        quotes = [
            make_quote(date(2024, 1, 2), 101, 106, 96, 103, 1100000),
            make_quote(date(2024, 1, 1), 100, 105, 95, 102, 1000000),
        ]

        series = analyzer.extract_price_series(quotes)

        # 验证排序（按日期升序）
        assert series["open"] == [100.0, 101.0]
        assert series["high"] == [105.0, 106.0]
        assert series["low"] == [95.0, 96.0]
        assert series["close"] == [102.0, 103.0]
        assert series["volume"] == [1000000.0, 1100000.0]

    def test_calculate_basic_stats(self):
        """测试基础统计计算"""
        analyzer = MockAnalyzer(name="test")
        quotes = [
            make_quote(date(2024, 1, 1), 100, 110, 90, 105, 1000000),
            make_quote(date(2024, 1, 2), 105, 115, 100, 110, 1200000),
            make_quote(date(2024, 1, 3), 110, 120, 105, 115, 1100000),
        ]

        stats = analyzer.calculate_basic_stats(quotes)

        assert stats["max_high"] == 120
        assert stats["min_low"] == 90
        assert stats["price_change_pct"] == pytest.approx(
            9.52, rel=0.01
        )  # (115-105)/105*100
        assert "avg_price" in stats
        assert "current_position" in stats

    def test_calculate_basic_stats_empty(self):
        """测试空数据统计"""
        analyzer = MockAnalyzer(name="test")
        stats = analyzer.calculate_basic_stats([])

        assert stats == {}

    def test_calculate_basic_stats_single_day(self):
        """测试单日数据统计"""
        analyzer = MockAnalyzer(name="test")
        quotes = [
            make_quote(date(2024, 1, 1), 100, 105, 95, 102, 1000000),
        ]

        stats = analyzer.calculate_basic_stats(quotes)

        # 单日数据，价格变化应为 0
        assert stats["price_change_pct"] == 0
