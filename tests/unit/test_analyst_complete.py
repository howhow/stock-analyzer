"""Analyst完整测试 - 异步优先、类型安全、防御性编程"""

from datetime import date
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest

from app.analysis.analyst import Analyst
from app.models.stock import DailyQuote, FinancialData, StockInfo


class TestAnalystFull:
    """分析师完整测试"""

    @pytest.fixture
    def analyst(self):
        """创建分析师实例"""
        return Analyst()

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
        """创建行情数据 - 60天数据"""
        quotes = []
        base_price = 10.0
        for i in range(60):
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

    def test_init(self, analyst):
        """测试初始化"""
        assert analyst is not None
        assert analyst.name == "analyst"

    @pytest.mark.asyncio
    async def test_analyze_success(self, analyst, stock_info, quotes, financial):
        """测试分析成功"""
        result = await analyst.analyze(stock_info, quotes, financial)

        assert result is not None
        assert result.analyzer_name == "analyst"

    @pytest.mark.asyncio
    async def test_analyze_insufficient_data(self, analyst, stock_info):
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

        result = await analyst.analyze(stock_info, quotes)

        assert result is not None
        # 应该有警告
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_analyze_without_financial(self, analyst, stock_info, quotes):
        """测试无财务数据分析"""
        result = await analyst.analyze(stock_info, quotes, None)

        assert result is not None
        assert result.analyzer_name == "analyst"

    @pytest.mark.asyncio
    async def test_analyze_with_trend(self, analyst, stock_info, financial):
        """测试趋势分析"""
        # 创建上升趋势数据
        quotes = []
        for i in range(60):
            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=10.0 + i * 0.2,
                    high=10.5 + i * 0.2,
                    low=9.8 + i * 0.2,
                    close=10.2 + i * 0.2,
                    volume=1000000 + i * 50000,
                    amount=(10.0 + i * 0.2) * (1000000 + i * 50000),
                )
            )

        result = await analyst.analyze(stock_info, quotes, financial)

        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_with_volatility(self, analyst, stock_info, financial):
        """测试波动性分析"""
        # 创建高波动性数据
        quotes = []
        for i in range(60):
            volatility = (i % 10) * 0.5  # 高波动
            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=10.0 + volatility,
                    high=10.5 + volatility,
                    low=9.5 - volatility,
                    close=10.0 + volatility * 0.5,
                    volume=1000000 + volatility * 100000,
                    amount=(10.0 + volatility) * (1000000 + volatility * 100000),
                )
            )

        result = await analyst.analyze(stock_info, quotes, financial)

        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_with_momentum(self, analyst, stock_info, financial):
        """测试动量分析"""
        # 创建动量变化数据
        quotes = []
        for i in range(60):
            momentum = i if i < 30 else 60 - i  # 先升后降
            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=10.0 + momentum * 0.1,
                    high=10.5 + momentum * 0.1,
                    low=9.8 + momentum * 0.1,
                    close=10.2 + momentum * 0.1,
                    volume=1000000 + momentum * 10000,
                    amount=(10.0 + momentum * 0.1) * (1000000 + momentum * 10000),
                )
            )

        result = await analyst.analyze(stock_info, quotes, financial)

        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_with_golden_cross(self, analyst, stock_info, financial):
        """测试金叉信号"""
        # 创建金叉数据（短期均线上穿长期均线）
        quotes = []
        for i in range(60):
            # 前期平稳，后期快速上涨
            price = 10.0 if i < 40 else 10.0 + (i - 40) * 0.5
            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=price,
                    high=price + 0.3,
                    low=price - 0.2,
                    close=price + 0.1,
                    volume=1000000 + i * 10000,
                    amount=price * (1000000 + i * 10000),
                )
            )

        result = await analyst.analyze(stock_info, quotes, financial)

        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_with_macd(self, analyst, stock_info, financial):
        """测试MACD分析"""
        # 创建MACD信号数据
        import numpy as np

        quotes = []
        for i in range(60):
            # 创建周期性波动
            price = 10.0 + 2.0 * np.sin(i * 0.2)
            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=price,
                    high=price + 0.3,
                    low=price - 0.2,
                    close=price + 0.1,
                    volume=1000000,
                    amount=price * 1000000,
                )
            )

        result = await analyst.analyze(stock_info, quotes, financial)

        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_with_rsi_extreme(self, analyst, stock_info, financial):
        """测试RSI极值"""
        # 创建超买/超卖数据
        quotes = []
        for i in range(60):
            # 持续上涨（超买）
            if i < 30:
                price = 10.0 + i * 0.5
            else:
                # 持续下跌（超卖）
                price = 25.0 - (i - 30) * 0.5

            quotes.append(
                DailyQuote(
                    stock_code="000001.SZ",
                    trade_date=date(2024, 1, 1) + pd.Timedelta(days=i),
                    open=price,
                    high=price + 0.3,
                    low=price - 0.2,
                    close=price,
                    volume=1000000,
                    amount=price * 1000000,
                )
            )

        result = await analyst.analyze(stock_info, quotes, financial)

        assert result is not None

    def test_extract_price_series(self, analyst, quotes):
        """测试提取价格序列"""
        prices = analyst.extract_price_series(quotes)

        assert isinstance(prices, dict)
        assert "close" in prices
        assert "high" in prices
        assert "low" in prices
        assert "open" in prices
        assert "volume" in prices
        assert len(prices["close"]) == len(quotes)

    def test_validate_data_sufficient(self, analyst, quotes):
        """测试数据验证 - 数据充足"""
        result = analyst.validate_data(quotes, min_days=20)
        assert result is True

    def test_validate_data_insufficient(self, analyst):
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

        result = analyst.validate_data(quotes, min_days=20)
        assert result is False

    def test_validate_data_empty(self, analyst):
        """测试数据验证 - 空数据"""
        result = analyst.validate_data([], min_days=20)
        assert result is False
