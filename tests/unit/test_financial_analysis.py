"""Financial Analysis完整测试 - 类型安全、防御性编程"""

import pytest
from datetime import date

from app.analysis.fundamental.financial import (
    analyze_profitability,
    analyze_solvency,
    analyze_growth,
    calculate_financial_score,
)
from app.models.stock import FinancialData


class TestFinancialAnalysis:
    """财务分析测试"""

    @pytest.fixture
    def financial_data(self):
        """创建财务数据"""
        return FinancialData(
            stock_code="000001.SZ",
            report_date=date(2024, 3, 31),
            revenue=1000000000.0,
            net_profit=100000000.0,
            total_assets=5000000000.0,
            total_liabilities=4000000000.0,
            operating_cash_flow=150000000.0
        )

    def test_analyze_profitability(self, financial_data):
        """测试盈利能力分析"""
        result = analyze_profitability(financial_data)
        
        assert isinstance(result, dict)
        assert "score" in result

    def test_analyze_solvency(self, financial_data):
        """测试偿债能力分析"""
        result = analyze_solvency(financial_data)
        
        assert isinstance(result, dict)
        assert "score" in result

    def test_analyze_growth(self, financial_data):
        """测试成长能力分析"""
        result = analyze_growth(financial_data)
        
        assert isinstance(result, dict)
        assert "score" in result

    def test_calculate_financial_score(self, financial_data):
        """测试财务评分计算"""
        result = calculate_financial_score(financial_data)
        
        assert isinstance(result, dict)
        assert "total_score" in result

    def test_analyze_profitability_empty(self):
        """测试盈利能力分析空数据"""
        result = analyze_profitability(None)
        
        assert isinstance(result, dict)

    def test_analyze_solvency_empty(self):
        """测试偿债能力分析空数据"""
        result = analyze_solvency(None)
        
        assert isinstance(result, dict)

    def test_analyze_growth_empty(self):
        """测试成长能力分析空数据"""
        result = analyze_growth(None)
        
        assert isinstance(result, dict)
