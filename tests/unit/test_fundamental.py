"""
基本面分析单元测试
"""

import pytest

from app.analysis.fundamental import (
    calculate_financial_score,
    calculate_industry_score,
    calculate_policy_score,
    get_industry_category,
)
from app.models.stock import FinancialData


class TestFinancialAnalysis:
    """财务分析测试"""

    def test_analyze_profitability(self):
        """测试盈利能力分析"""
        financial = FinancialData(
            stock_code="600519.SH",
            report_date="2026-03-31",
            roe=22.5,
            net_profit=5000000000,
            pe_ratio=25.0,
            pb_ratio=3.5,
        )

        result = calculate_financial_score(financial)

        assert "total_score" in result
        assert "profitability" in result
        assert "solvency" in result
        assert "growth" in result

        # ROE > 20 应该获得较高分数
        assert result["profitability"]["score"] >= 70

    def test_analyze_solvency(self):
        """测试偿债能力分析"""
        financial = FinancialData(
            stock_code="600519.SH",
            report_date="2026-03-31",
            debt_ratio=35.0,
            total_assets=10000000000,
            total_liabilities=3500000000,
        )

        result = calculate_financial_score(financial)

        # 低负债率应该获得较高分数
        assert result["solvency"]["score"] >= 60

    def test_empty_financial_data(self):
        """测试空财务数据"""
        result = calculate_financial_score(None)

        assert result["total_score"] == 0
        assert "无数据" in result["profitability"]["details"]


class TestIndustryAnalysis:
    """行业分析测试"""

    def test_get_industry_category(self):
        """测试行业分类"""
        assert get_industry_category("软件开发") == "科技"
        assert get_industry_category("白酒生产") == "消费"
        assert get_industry_category("商业银行") == "金融"
        assert get_industry_category("医药制造") == "医药"
        assert get_industry_category("未知行业") == "default"

    def test_calculate_industry_score(self):
        """测试行业评分"""
        result = calculate_industry_score("白酒", industry_rank=5)

        assert "total_score" in result
        assert "position" in result
        assert "category" in result

        # 龙头企业应该获得较高分数
        assert result["total_score"] >= 80
        assert result["position"] == "龙头"

    def test_unknown_industry(self):
        """测试未知行业"""
        result = calculate_industry_score(None)

        assert result["category"] == "default"
        assert result["total_score"] >= 50  # 默认中等分数


class TestPolicyAnalysis:
    """政策分析测试"""

    def test_get_policy_sensitivity(self):
        """测试政策敏感度"""
        assert get_policy_sensitivity("芯片制造") == "高敏感"
        assert get_policy_sensitivity("医药研发") == "高敏感"
        assert get_policy_sensitivity("白酒生产") == "低敏感"
        assert get_policy_sensitivity("商业银行") == "中敏感"

    def test_calculate_policy_score(self):
        """测试政策评分"""
        # 科技行业（高敏感）
        result = calculate_policy_score("软件开发")
        assert "total_score" in result
        assert "sensitivity" in result

        # 消费行业（低敏感）
        result_consumer = calculate_policy_score("白酒")
        assert result_consumer["sensitivity"] == "低敏感"

    def test_policy_with_events(self):
        """测试政策事件影响"""
        policy_events = [
            {"impact": "positive", "description": "政策利好"},
            {"impact": "positive", "description": "减税政策"},
        ]

        result = calculate_policy_score("科技", policy_events=policy_events)

        # 利好政策应该提高分数
        assert result["total_score"] >= 60
