"""System Analyzer完整测试 - 异步优先、类型安全、防御性编程"""

import pytest
import pandas as pd
from datetime import date
from unittest.mock import Mock, AsyncMock, patch

from app.analysis.system import SystemAnalyzer
from app.models.stock import StockInfo, DailyQuote, FinancialData


class TestSystemAnalyzerFull:
    """系统分析器完整测试"""

    @pytest.fixture
    def system_analyzer(self):
        """创建系统分析器实例"""
        return SystemAnalyzer()

    @pytest.fixture
    def stock_info(self):
        """创建股票信息"""
        return StockInfo(
            code="000001.SZ",
            name="平安银行",
            industry="银行",
            market="SZ",
            list_date=date(1991, 4, 3),
        )

    @pytest.fixture
    def quotes(self):
        """创建行情数据 - 30天数据"""
        quotes = []
        base_price = 10.0
        for i in range(30):
            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=base_price + i * 0.1,
                    high=base_price + i * 0.1 + 0.5,
                    low=base_price + i * 0.1 - 0.3,
                    close=base_price + i * 0.1 + 0.2,
                    volume=1000000 + i * 10000,
                    amount=(base_price + i * 0.1) * (1000000 + i * 10000),
                )
            )
        return quotes

    @pytest.fixture
    def financial(self):
        """创建财务数据"""
        return FinancialData(
            stock_code="000001.SZ",
            report_date=date(2024, 3, 31),
            revenue=1000000000.0,
            net_profit=100000000.0,
            total_assets=5000000000.0,
            total_liabilities=4000000000.0,
        )

    def test_init(self, system_analyzer):
        """测试初始化"""
        assert system_analyzer is not None
        assert system_analyzer.name == "system"
        assert system_analyzer.analyst is not None
        assert system_analyzer.trader is not None

    @pytest.mark.asyncio
    async def test_analyze_long_term(
        self, system_analyzer, stock_info, quotes, financial
    ):
        """测试长期分析"""
        result = await system_analyzer.analyze(
            stock_info, quotes, financial, analysis_type="long"
        )

        assert result is not None
        assert result.analyzer_name == "system"

    @pytest.mark.asyncio
    async def test_analyze_short_term(
        self, system_analyzer, stock_info, quotes, financial
    ):
        """测试短期分析"""
        result = await system_analyzer.analyze(
            stock_info, quotes, financial, analysis_type="short"
        )

        assert result is not None
        assert result.analyzer_name == "system"

    @pytest.mark.asyncio
    async def test_analyze_insufficient_data(self, system_analyzer, stock_info):
        """测试数据不足"""
        # 只有10天数据，不足20天
        quotes = []
        for i in range(10):
            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=10.0,
                    high=10.5,
                    low=9.8,
                    close=10.2,
                    volume=1000000,
                    amount=10200000.0,
                )
            )

        result = await system_analyzer.analyze(stock_info, quotes)

        assert result is not None
        # 应该有警告
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_analyze_without_financial(self, system_analyzer, stock_info, quotes):
        """测试无财务数据分析"""
        result = await system_analyzer.analyze(
            stock_info, quotes, None, analysis_type="long"
        )

        assert result is not None
        assert result.analyzer_name == "system"

    @pytest.mark.asyncio
    async def test_analyze_with_bullish_trend(
        self, system_analyzer, stock_info, financial
    ):
        """测试牛市趋势分析"""
        # 创建上升趋势数据
        quotes = []
        for i in range(30):
            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=10.0 + i * 0.3,
                    high=10.5 + i * 0.3,
                    low=9.8 + i * 0.3,
                    close=10.2 + i * 0.3,
                    volume=1000000 + i * 100000,
                    amount=(10.0 + i * 0.3) * (1000000 + i * 100000),
                )
            )

        result = await system_analyzer.analyze(
            stock_info, quotes, financial, analysis_type="long"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_with_bearish_trend(
        self, system_analyzer, stock_info, financial
    ):
        """测试熊市趋势分析"""
        # 创建下降趋势数据
        quotes = []
        for i in range(30):
            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=20.0 - i * 0.3,
                    high=20.5 - i * 0.3,
                    low=19.8 - i * 0.3,
                    close=20.0 - i * 0.3,
                    volume=1000000 + i * 100000,
                    amount=(20.0 - i * 0.3) * (1000000 + i * 100000),
                )
            )

        result = await system_analyzer.analyze(
            stock_info, quotes, financial, analysis_type="short"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_integration(
        self, system_analyzer, stock_info, quotes, financial
    ):
        """测试分析师和交易员集成"""
        result = await system_analyzer.analyze(
            stock_info, quotes, financial, analysis_type="long"
        )

        assert result is not None
        # 应该包含analyst和trader的结果
        assert "analyst" in result.details
        assert "trader" in result.details

    def test_validate_data_sufficient(self, system_analyzer, quotes):
        """测试数据验证 - 数据充足"""
        result = system_analyzer.validate_data(quotes, min_days=20)
        assert result is True

    def test_validate_data_insufficient(self, system_analyzer):
        """测试数据验证 - 数据不足"""
        quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                high=10.5,
                low=9.8,
                close=10.2,
                volume=1000000,
                amount=10200000.0,
            )
            for _ in range(10)
        ]

        result = system_analyzer.validate_data(quotes, min_days=20)
        assert result is False
