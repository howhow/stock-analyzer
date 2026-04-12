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

    def test_is_valid_false_close_out_of_range(self):
        """测试数据合理性 - 收盘价超出范围"""
        quote = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            open=1840.00,
            high=1860.00,
            low=1835.00,
            close=1870.00,  # 超出最高价
            source="tushare",
        )

        assert quote.is_valid() is False

    def test_get_quality_label(self):
        """测试质量标签"""
        # 高质量
        quote_high = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            close=1850.50,
            source="tushare",
            quality_score=0.95,
        )
        assert quote_high.get_quality_label() == "high"

        # 中质量
        quote_medium = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            close=1850.50,
            source="tushare",
            quality_score=0.75,
        )
        assert quote_medium.get_quality_label() == "medium"

        # 低质量
        quote_low = StandardQuote(
            code="600519.SH",
            trade_date=date(2024, 1, 1),
            close=1850.50,
            source="tushare",
            quality_score=0.50,
        )
        assert quote_low.get_quality_label() == "low"

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
        assert df is None

    def test_get_first_and_last_quote(self):
        """测试获取首尾数据"""
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

        first = batch.get_first_quote()
        last = batch.get_last_quote()

        assert first is not None
        assert first.close == 1850.50
        assert last is not None
        assert last.close == 1860.00

    def test_empty_batch_first_last_none(self):
        """测试空批次的首尾数据"""
        batch = StandardQuoteBatch(
            code="600519.SH",
            quotes=[],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            source="tushare",
        )

        assert batch.get_first_quote() is None
        assert batch.get_last_quote() is None
