"""测试标准行情数据模型"""

from datetime import date

import pytest

from framework.models.quote import StandardQuote, StandardQuoteBatch


class TestStandardQuote:
    """测试 StandardQuote 模型"""

    def test_create_with_required_fields(self):
        """测试创建 - 仅必填字段"""
        quote = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            close=1850.50,
            source="tushare",
        )

        assert quote.code == "600519.SH"
        assert quote.trade_date == date(2024, 1, 1)
        assert quote.close == 1850.50
        assert quote.source == "tushare"
        assert quote.open is None
        assert quote.high is None
        assert quote.low is None
        assert quote.volume is None

    def test_create_with_all_fields(self):
        """测试创建 - 所有字段"""
        quote = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            open=1840.00,
            high=1860.00,
            low=1835.00,
            close=1850.50,
            volume=12345678,
            amount=22.5e9,
            turnover_rate=0.5,
            source="tushare",
            completeness=0.95,
            quality_score=0.90,
        )

        assert quote.open == 1840.00
        assert quote.high == 1860.00
        assert quote.low == 1835.00
        assert quote.volume == 12345678
        assert quote.amount == 22.5e9
        assert quote.turnover_rate == 0.5
        assert quote.completeness == 0.95
        assert quote.quality_score == 0.90

    def test_is_complete_true(self):
        """测试完整性检查 - 完整"""
        quote = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            open=1840.00,
            high=1860.00,
            low=1835.00,
            close=1850.50,
            volume=12345678,
            source="tushare",
        )

        assert quote.is_complete() is True

    def test_is_complete_false(self):
        """测试完整性检查 - 不完整"""
        quote = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            close=1850.50,
            source="tushare",
        )

        assert quote.is_complete() is False

    def test_is_valid_true(self):
        """测试数据合理性 - 合理"""
        quote = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            open=1840.00,
            high=1860.00,
            low=1835.00,
            close=1850.50,
            volume=12345678,
            source="tushare",
        )

        assert quote.is_valid() is True

    def test_is_valid_false_high_less_than_low(self):
        """测试数据合理性 - 最高价小于最低价"""
        quote = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            open=1840.00,
            high=1830.00,  # 最高价 < 最低价
            low=1835.00,
            close=1850.50,
            source="tushare",
        )

        assert quote.is_valid() is False

    def test_to_dict(self):
        """测试转换为字典"""
        quote = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            close=1850.50,
            source="tushare",
        )

        data = quote.to_dict()

        assert isinstance(data, dict)
        assert data["code"] == "600519.SH"
        assert "trade_date" in data or "date" in data
        assert data["close"] == 1850.50


class TestStandardQuoteBatch:
    """测试 StandardQuoteBatch 模型"""

    def test_create_batch(self):
        """测试创建批次"""
        quotes = [
            StandardQuote(
                code="600519.SH",
                trade_date=date(2024, 1, 1),
                close=1850.50,
                source="tushare",
            ),
            StandardQuote(
                code="600519.SH",
                trade_date=date(2024, 1, 2),
                close=1860.00,
                source="tushare",
            ),
        ]

        batch = StandardQuoteBatch(
            code="600519.SH",
            quotes=quotes,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
            source="tushare",
        )

        assert batch.code == "600519.SH"
        assert len(batch.quotes) == 2
        assert batch.count == 2

    def test_to_dataframe(self):
        """测试转换为 DataFrame"""
        quotes = [
            StandardQuote(
                code="600519.SH",
                trade_date=date(2024, 1, 1),
                close=1850.50,
                volume=1000000,
                source="tushare",
            ),
            StandardQuote(
                code="600519.SH",
                trade_date=date(2024, 1, 2),
                close=1860.00,
                volume=1100000,
                source="tushare",
            ),
        ]

        batch = StandardQuoteBatch(
            code="600519.SH",
            quotes=quotes,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
            source="tushare",
        )

        df = batch.to_dataframe()

        assert df is not None
        assert len(df) == 2
        assert "close" in df.columns
        assert "volume" in df.columns

    def test_empty_batch(self):
        """测试空批次"""
        batch = StandardQuoteBatch(
            code="600519.SH",
            quotes=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            source="tushare",
        )

        assert batch.count == 0
        df = batch.to_dataframe()
        # 空列表返回 None
        if len(batch.quotes) == 0:
            assert df is None or len(df) == 0
