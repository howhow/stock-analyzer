"""
交易员模块完整测试

覆盖率目标: ≥ 95%
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock

from app.analysis.trader import Trader
from app.models.stock import DailyQuote, FinancialData, StockInfo


class TestTraderInit:
    """Trader 初始化测试"""
    
    def test_init_success(self):
        """测试成功初始化"""
        trader = Trader()
        assert trader.name == "trader"
        assert isinstance(trader, Trader)


class TestTraderAnalyze:
    """Trader 分析测试"""
    
    @pytest.fixture
    def trader(self):
        return Trader()
    
    @pytest.fixture
    def stock_info(self):
        return StockInfo(
            code="600519",
            name="贵州茅台",
            market="SH"
        )
    
    @pytest.fixture
    def quotes(self):
        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(30):
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=1800.0 + i,
                close=1805.0 + i,
                high=1810.0 + i,
                low=1795.0 + i,
                volume=1000000.0,
                amount=1800000000.0
            )
            quotes.append(quote)
        return quotes
    
    @pytest.mark.asyncio
    async def test_analyze_success(self, trader, stock_info, quotes):
        """测试成功分析"""
        result = await trader.analyze(stock_info, quotes)
        
        assert result is not None
        assert result.analyzer_name == "trader"
        assert "total" in result.scores
        assert "recommendation" in result.details
    
    @pytest.mark.asyncio
    async def test_analyze_insufficient_data(self, trader, stock_info):
        """测试数据不足"""
        quotes = []
        for i in range(10):
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=date(2024, 1, 1) + timedelta(days=i),
                open=1800.0,
                close=1805.0,
                high=1810.0,
                low=1795.0,
                volume=1000000.0,
                amount=1800000000.0
            )
            quotes.append(quote)
        
        result = await trader.analyze(stock_info, quotes)
        
        assert "数据不足" in result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_analyze_with_financial(self, trader, stock_info, quotes):
        """测试带财务数据分析"""
        financial = FinancialData(
            stock_code="600519.SH",
            report_date=date(2023, 12, 31),
            revenue=127500000000.0,
            net_profit=62720000000.0,
            roe=31.5
        )
        
        result = await trader.analyze(stock_info, quotes, financial)
        
        assert result is not None
        assert "risk_level" in result.scores
    
    @pytest.mark.asyncio
    async def test_analyze_recommendation(self, trader, stock_info, quotes):
        """测试交易建议"""
        result = await trader.analyze(stock_info, quotes)
        
        assert "recommendation" in result.details
        assert result.details["recommendation"] in ["strong_buy", "buy", "hold", "sell", "strong_sell"]
        assert "confidence" in result.details
        assert 0 <= result.details["confidence"] <= 100


class TestTraderScoring:
    """评分计算测试"""
    
    @pytest.fixture
    def trader(self):
        return Trader()
    
    @pytest.mark.asyncio
    async def test_signal_strength_calculation(self, trader):
        """测试信号强度计算"""
        stock_info = StockInfo(code="600519", name="贵州茅台", market="SH")
        
        # 创建上升趋势数据
        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(30):
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=1800.0 + i * 5,
                close=1805.0 + i * 5,
                high=1810.0 + i * 5,
                low=1795.0 + i * 5,
                volume=1000000.0,
                amount=1800000000.0
            )
            quotes.append(quote)
        
        result = await trader.analyze(stock_info, quotes)
        
        assert "signal_strength" in result.scores
        assert 0 <= result.scores["signal_strength"] <= 100
    
    @pytest.mark.asyncio
    async def test_opportunity_quality_calculation(self, trader):
        """测试机会质量计算"""
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
                amount=1800000000.0
            )
            quotes.append(quote)
        
        result = await trader.analyze(stock_info, quotes)
        
        assert "opportunity_quality" in result.scores
        assert 0 <= result.scores["opportunity_quality"] <= 100
    
    @pytest.mark.asyncio
    async def test_risk_level_calculation(self, trader):
        """测试风险等级计算"""
        stock_info = StockInfo(code="600519", name="贵州茅台", market="SH")
        
        # 创建高波动率数据
        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(30):
            volatility = 50 if i % 2 == 0 else -50
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=1800.0,
                close=1800.0 + volatility,
                high=1850.0 + abs(volatility),
                low=1750.0 - abs(volatility),
                volume=1000000.0,
                amount=1800000000.0
            )
            quotes.append(quote)
        
        result = await trader.analyze(stock_info, quotes)
        
        assert "risk_level" in result.scores
        # 高波动率应该有较高的风险等级
        assert result.scores["risk_level"] > 50


class TestTraderRecommendations:
    """交易建议测试"""
    
    @pytest.fixture
    def trader(self):
        return Trader()
    
    @pytest.mark.asyncio
    async def test_buy_recommendation(self, trader):
        """测试买入建议"""
        stock_info = StockInfo(code="600519", name="贵州茅台", market="SH")
        
        # 创建强势上涨趋势
        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(30):
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=1800.0 + i * 10,
                close=1810.0 + i * 10,
                high=1815.0 + i * 10,
                low=1795.0 + i * 10,
                volume=2000000.0,  # 高成交量
                amount=3600000000.0
            )
            quotes.append(quote)
        
        result = await trader.analyze(stock_info, quotes)
        
        # 强势上涨应该得到买入建议
        assert result.details["recommendation"] in ["strong_buy", "buy"]
    
    @pytest.mark.asyncio
    async def test_sell_recommendation(self, trader):
        """测试卖出建议"""
        stock_info = StockInfo(code="600519", name="贵州茅台", market="SH")
        
        # 创建弱势下跌趋势
        quotes = []
        base_date = date(2024, 1, 1)
        for i in range(30):
            quote = DailyQuote(
                stock_code="600519.SH",
                trade_date=base_date + timedelta(days=i),
                open=2000.0 - i * 10,
                close=1990.0 - i * 10,
                high=2005.0 - i * 10,
                low=1985.0 - i * 10,
                volume=2000000.0,
                amount=3600000000.0
            )
            quotes.append(quote)
        
        result = await trader.analyze(stock_info, quotes)
        
        # 弱势下跌应该得到卖出建议
        assert result.details["recommendation"] in ["sell", "strong_sell", "hold"]


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.analysis.trader", "--cov-report=term-missing"])
