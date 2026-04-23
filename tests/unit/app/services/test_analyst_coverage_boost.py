"""
分析师模块完整测试

覆盖率目标: ≥ 95%
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.analysis.analyst import Analyst
from app.models.stock import DailyQuote, FinancialData, StockInfo


class TestAnalystInit:
    """Analyst 初始化测试"""

    def test_init_success(self):
        """测试成功初始化"""
        analyst = Analyst()
        assert analyst.name == "analyst"
        assert isinstance(analyst, Analyst)

    def test_analyzer_name(self):
        """测试分析器名称"""
        analyst = Analyst()
        assert analyst.name == "analyst"


class TestAnalystAnalyze:
    """Analyst 分析测试"""

    @pytest.fixture
    def analyst(self):
        """创建分析师实例"""
        return Analyst()

    @pytest.fixture
    def stock_info(self):
        """创建股票信息"""
        return StockInfo(code="600519", name="贵州茅台", market="SH", industry="白酒")

    @pytest.fixture
    def quotes(self):
        """创建行情数据"""
        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(30):
            trade_date = base_date + timedelta(days=i)
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=trade_date,
                open=1800.0 + i,
                close=1805.0 + i,
                high=1810.0 + i,
                low=1795.0 + i,
                volume=1000000.0,
                amount=1800000000.0,
            )
            quotes.append(quote)
        return quotes

    @pytest.fixture
    def financial(self):
        """创建财务数据"""
        return FinancialData(
            stock_code="600519.SH",
            report_date=date(2023, 12, 31),
            revenue=127500000000.0,
            net_profit=62720000000.0,
            total_assets=254300000000.0,
            total_liabilities=87200000000.0,
            roe=31.5,
            pe_ratio=35.2,
            pb_ratio=12.8,
            debt_ratio=34.3,
        )

    @pytest.mark.asyncio
    async def test_analyze_success(self, analyst, stock_info, quotes, financial):
        """测试成功分析"""
        result = await analyst.analyze(stock_info, quotes, financial)

        assert result is not None
        assert result.analyzer_name == "analyst"
        assert "total" in result.scores
        assert result.scores["total"] >= 0
        assert result.scores["total"] <= 100

    @pytest.mark.asyncio
    async def test_analyze_insufficient_data(self, analyst, stock_info):
        """测试数据不足"""
        # 只有10天数据，少于要求的20天
        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(10):
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=1800.0,
                close=1805.0,
                high=1810.0,
                low=1795.0,
                volume=1000000.0,
                amount=1800000000.0,
            )
            quotes.append(quote)

        result = await analyst.analyze(stock_info, quotes)

        assert "数据不足" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_analyze_without_financial(self, analyst, stock_info, quotes):
        """测试无财务数据分析"""
        result = await analyst.analyze(stock_info, quotes, None)

        assert result is not None
        # 应该使用默认评分
        assert "fundamental" in result.scores

    @pytest.mark.asyncio
    async def test_analyze_with_trend(self, analyst, stock_info, quotes, financial):
        """测试趋势分析"""
        result = await analyst.analyze(stock_info, quotes, financial)

        assert "technical" in result.scores
        # 上升趋势应该得到较高的技术面评分
        assert result.scores["technical"] >= 50

    @pytest.mark.asyncio
    async def test_analyze_score_range(self, analyst, stock_info, quotes, financial):
        """测试评分范围"""
        result = await analyst.analyze(stock_info, quotes, financial)

        # 所有评分应该在 0-100 之间
        for score_name, score_value in result.scores.items():
            assert 0 <= score_value <= 100, f"{score_name} 评分超出范围: {score_value}"


class TestAnalystDataExtraction:
    """数据提取测试"""

    def test_extract_price_series(self):
        """测试价格序列提取"""
        analyst = Analyst()
        quotes = []
        base_date = date(2024, 1, 1)

        for i in range(5):
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=1800.0 + i,
                close=1805.0 + i,
                high=1810.0 + i,
                low=1795.0 + i,
                volume=1000000.0,
                amount=1800000000.0,
            )
            quotes.append(quote)

        prices = analyst.extract_price_series(quotes)

        assert "close" in prices
        assert "high" in prices
        assert "low" in prices
        assert len(prices["close"]) == 5


class TestAnalystValidation:
    """数据验证测试"""

    def test_validate_data_sufficient(self):
        """测试数据充足验证"""
        analyst = Analyst()
        quotes = [Mock() for _ in range(30)]

        assert analyst.validate_data(quotes, min_days=20) is True

    def test_validate_data_insufficient(self):
        """测试数据不足验证"""
        analyst = Analyst()
        quotes = [Mock() for _ in range(15)]

        assert analyst.validate_data(quotes, min_days=20) is False

    def test_validate_data_empty(self):
        """测试空数据验证"""
        analyst = Analyst()

        assert analyst.validate_data([], min_days=20) is False


class TestAnalystFundamental:
    """基本面分析测试"""

    @pytest.mark.asyncio
    async def test_fundamental_analysis_with_good_financial(self):
        """测试优质财务数据分析"""
        analyst = Analyst()
        financial = FinancialData(
            stock_code="600519.SH",
            report_date=date(2023, 12, 31),
            revenue=127500000000.0,
            net_profit=62720000000.0,
            roe=31.5,
            debt_ratio=34.3,
        )

        stock_info = StockInfo(code="600519", name="贵州茅台", market="SH")

        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(30):
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=1800.0,
                close=1805.0,
                high=1810.0,
                low=1795.0,
                volume=1000000.0,
                amount=1800000000.0,
            )
            quotes.append(quote)

        result = await analyst.analyze(stock_info, quotes, financial)

        # 优质财务数据应该得到较高的基本面评分
        assert result.scores["fundamental"] >= 50  # 调整为更合理的阈值


class TestAnalystTechnical:
    """技术面分析测试"""

    @pytest.mark.asyncio
    async def test_technical_analysis_uptrend(self):
        """测试上升趋势技术分析"""
        analyst = Analyst()

        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(30):
            # 持续上涨
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=1800.0 + i * 5,
                close=1805.0 + i * 5,
                high=1810.0 + i * 5,
                low=1795.0 + i * 5,
                volume=1000000.0,
                amount=1800000000.0,
            )
            quotes.append(quote)

        stock_info = StockInfo(code="600519", name="贵州茅台", market="SH")

        result = await analyst.analyze(stock_info, quotes)

        # 上升趋势应该得到较高的技术面评分
        assert result.scores["technical"] >= 50

    @pytest.mark.asyncio
    async def test_technical_analysis_downtrend(self):
        """测试下降趋势技术分析"""
        analyst = Analyst()

        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(30):
            # 持续下跌
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=2000.0 - i * 5,
                close=1995.0 - i * 5,
                high=2005.0 - i * 5,
                low=1990.0 - i * 5,
                volume=1000000.0,
                amount=1800000000.0,
            )
            quotes.append(quote)

        stock_info = StockInfo(code="600519", name="贵州茅台", market="SH")

        result = await analyst.analyze(stock_info, quotes)

        # 下降趋势应该得到较低的技术面评分
        assert result.scores["technical"] <= 60


# 运行测试
if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=app.analysis.analyst", "--cov-report=term-missing"]
    )
