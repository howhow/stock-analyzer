"""TushareQuoteMapper 测试

覆盖数据转换核心逻辑 — 用户每次查询都走这里，必须 100% 覆盖。
"""

from datetime import date

import pandas as pd
import pytest

from framework.models.quote import StandardQuote
from plugins.data_sources.tushare.mapper import TushareQuoteMapper


class TestMapToQuotes:
    """测试 map_to_quotes 主入口"""

    def test_empty_dataframe(self):
        """空 DataFrame 应返回空列表"""
        result = TushareQuoteMapper.map_to_quotes(pd.DataFrame())
        assert result == []

    def test_none_input(self):
        """None 输入应返回空列表"""
        result = TushareQuoteMapper.map_to_quotes(None)
        assert result == []

    def test_single_row_success(self):
        """单行数据成功转换"""
        df = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "trade_date": ["20240101"],
                "open": [100.0],
                "high": [105.0],
                "low": [99.0],
                "close": [103.0],
                "vol": [10000.0],
                "amount": [1030000.0],
            }
        )

        result = TushareQuoteMapper.map_to_quotes(df)

        assert len(result) == 1
        quote = result[0]
        assert isinstance(quote, StandardQuote)
        assert quote.code == "600519.SH"
        assert quote.close == 103.0
        assert quote.trade_date == date(2024, 1, 1)

    def test_multiple_rows_sorted(self):
        """多行数据按日期升序排序"""
        df = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "600519.SH"],
                "trade_date": ["20240102", "20240101"],
                "open": [101.0, 100.0],
                "high": [106.0, 105.0],
                "low": [100.0, 99.0],
                "close": [104.0, 103.0],
                "vol": [9000.0, 10000.0],
                "amount": [936000.0, 1030000.0],
            }
        )

        result = TushareQuoteMapper.map_to_quotes(df)

        assert len(result) == 2
        # 验证按日期升序排序
        assert result[0].trade_date == date(2024, 1, 1)
        assert result[1].trade_date == date(2024, 1, 2)

    def test_row_with_exception_skipped(self):
        """异常行应被跳过，继续处理后续行"""
        df = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "600519.SH"],
                "trade_date": ["invalid_date", "20240101"],
                "open": [100.0, 100.0],
                "high": [105.0, 105.0],
                "low": [99.0, 99.0],
                "close": [103.0, 103.0],
                "vol": [10000.0, 10000.0],
                "amount": [1030000.0, 1030000.0],
            }
        )

        result = TushareQuoteMapper.map_to_quotes(df)

        # 第一行异常被跳过，第二行成功
        assert len(result) == 1
        assert result[0].trade_date == date(2024, 1, 1)

    def test_missing_optional_fields(self):
        """缺少可选字段应使用默认值"""
        df = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "trade_date": ["20240101"],
                "close": [103.0],
            }
        )

        result = TushareQuoteMapper.map_to_quotes(df)

        assert len(result) == 1
        quote = result[0]
        assert quote.open is None
        assert quote.high is None
        assert quote.volume is None

    def test_source_parameter(self):
        """自定义 source 参数"""
        df = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "trade_date": ["20240101"],
                "close": [103.0],
            }
        )

        result = TushareQuoteMapper.map_to_quotes(df, source="custom")
        assert result[0].source == "custom"


class TestMapRowToQuote:
    """测试 _map_row_to_quote 行级转换"""

    def test_complete_data(self):
        """完整数据转换"""
        row = pd.Series(
            {
                "ts_code": "600519.SH",
                "trade_date": "20240101",
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.0,
                "vol": 10000.0,
                "amount": 1030000.0,
            }
        )

        quote = TushareQuoteMapper._map_row_to_quote(row, "tushare")

        assert quote is not None
        assert quote.code == "600519.SH"
        assert quote.open == 100.0
        assert quote.high == 105.0
        assert quote.low == 99.0
        assert quote.close == 103.0
        assert quote.volume == 10000
        assert quote.amount == 1030000.0
        assert quote.source == "tushare"

    def test_integer_volume(self):
        """成交量转为整数"""
        row = pd.Series(
            {
                "ts_code": "600519.SH",
                "trade_date": "20240101",
                "close": 103.0,
                "vol": 10000.7,  # 浮点数
            }
        )

        quote = TushareQuoteMapper._map_row_to_quote(row, "tushare")
        assert quote.volume == 10000  # 截断为整数

    def test_trade_date_formats(self):
        """多种日期格式解析"""
        test_cases = [
            ("20240101", date(2024, 1, 1)),
            ("2024-01-01", date(2024, 1, 1)),
        ]

        for date_str, expected in test_cases:
            row = pd.Series(
                {
                    "ts_code": "600519.SH",
                    "trade_date": date_str,
                    "close": 100.0,
                }
            )
            quote = TushareQuoteMapper._map_row_to_quote(row, "tushare")
            assert quote.trade_date == expected, f"Failed for {date_str}"

    def test_missing_required_field(self):
        """缺少必填字段返回 None"""
        row = pd.Series(
            {
                "ts_code": "600519.SH",
                "trade_date": "20240101",
                # 缺少 close
            }
        )

        quote = TushareQuoteMapper._map_row_to_quote(row, "tushare")
        assert quote is None

    def test_invalid_trade_date(self):
        """无效日期返回 None"""
        row = pd.Series(
            {
                "ts_code": "600519.SH",
                "trade_date": "invalid",
                "close": 100.0,
            }
        )

        quote = TushareQuoteMapper._map_row_to_quote(row, "tushare")
        assert quote is None

    def test_missing_code(self):
        """缺少股票代码返回 None"""
        row = pd.Series(
            {
                "trade_date": "20240101",
                "close": 100.0,
            }
        )

        quote = TushareQuoteMapper._map_row_to_quote(row, "tushare")
        assert quote is None


class TestCalculateCompleteness:
    """测试 _calculate_completeness 完整度计算"""

    def test_complete_data(self):
        """完整数据 100%"""
        completeness = TushareQuoteMapper._calculate_completeness(
            open_price=100.0,
            high_price=105.0,
            low_price=99.0,
            close_price=103.0,
            volume=10000,
            amount=1030000.0,
        )
        assert completeness == 1.0

    def test_partial_data(self):
        """部分缺失"""
        completeness = TushareQuoteMapper._calculate_completeness(
            open_price=100.0,
            high_price=None,
            low_price=99.0,
            close_price=103.0,
            volume=None,
            amount=1030000.0,
        )
        # 价格 3/4 * 0.6 = 0.45, 成交 1/2 * 0.4 = 0.2, 总计 0.65
        assert completeness == 0.65

    def test_all_none(self):
        """全部 None"""
        completeness = TushareQuoteMapper._calculate_completeness(
            open_price=None,
            high_price=None,
            low_price=None,
            close_price=None,
            volume=None,
            amount=None,
        )
        assert completeness == 0.0


class TestCalculateQualityScore:
    """测试 _calculate_quality_score 质量评分"""

    def test_perfect_data(self):
        """完美数据 1.0"""
        score = TushareQuoteMapper._calculate_quality_score(
            open_price=100.0,
            high_price=105.0,
            low_price=99.0,
            close_price=103.0,
        )
        assert score == 1.0

    def test_missing_price(self):
        """缺少价格字段 0.5"""
        score = TushareQuoteMapper._calculate_quality_score(
            open_price=100.0,
            high_price=None,
            low_price=99.0,
            close_price=103.0,
        )
        assert score == 0.5

    def test_negative_price(self):
        """负价格降低评分"""
        score = TushareQuoteMapper._calculate_quality_score(
            open_price=-100.0,
            high_price=105.0,
            low_price=99.0,
            close_price=103.0,
        )
        assert score < 1.0

    def test_high_low_violation(self):
        """high < low 降低评分"""
        score = TushareQuoteMapper._calculate_quality_score(
            open_price=100.0,
            high_price=99.0,  # 错误：high < low
            low_price=105.0,
            close_price=103.0,
        )
        assert score < 1.0

    def test_close_out_of_range(self):
        """收盘价超出范围降低评分"""
        score = TushareQuoteMapper._calculate_quality_score(
            open_price=100.0,
            high_price=105.0,
            low_price=99.0,
            close_price=110.0,  # 超出 high
        )
        assert score < 1.0


class TestExtractMethods:
    """测试提取方法"""

    def test_extract_string(self):
        """提取字符串"""
        row = pd.Series({"field": "value"})
        assert TushareQuoteMapper._extract_string(row, "field") == "value"

    def test_extract_string_none(self):
        """提取 None"""
        row = pd.Series({"field": None})
        assert TushareQuoteMapper._extract_string(row, "field") is None

    def test_extract_string_nan(self):
        """提取 NaN"""
        row = pd.Series({"field": float("nan")})
        assert TushareQuoteMapper._extract_string(row, "field") is None

    def test_extract_float(self):
        """提取浮点数"""
        row = pd.Series({"field": 100.5})
        assert TushareQuoteMapper._extract_float(row, "field") == 100.5

    def test_extract_float_invalid(self):
        """提取无效浮点数"""
        row = pd.Series({"field": "invalid"})
        assert TushareQuoteMapper._extract_float(row, "field") is None

    def test_extract_int(self):
        """提取整数"""
        row = pd.Series({"field": 10000.7})
        assert TushareQuoteMapper._extract_int(row, "field") == 10000

    def test_extract_date_ymd(self):
        """提取 YYYYMMDD 日期"""
        row = pd.Series({"field": "20240101"})
        assert TushareQuoteMapper._extract_date(row, "field") == date(2024, 1, 1)

    def test_extract_date_iso(self):
        """提取 ISO 日期"""
        row = pd.Series({"field": "2024-01-01"})
        assert TushareQuoteMapper._extract_date(row, "field") == date(2024, 1, 1)

    def test_extract_date_invalid(self):
        """提取无效日期"""
        row = pd.Series({"field": "invalid"})
        assert TushareQuoteMapper._extract_date(row, "field") is None
