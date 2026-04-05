"""Industry Analysis完整测试 - 类型安全、防御性编程"""

import pytest

from app.analysis.fundamental.industry import (
    get_industry_category,
    calculate_industry_score,
)


class TestIndustryAnalysis:
    """行业分析测试"""

    def test_get_industry_category_known(self):
        """测试已知行业类别"""
        result = get_industry_category("银行")
        
        assert isinstance(result, str)

    def test_get_industry_category_unknown(self):
        """测试未知行业类别"""
        result = get_industry_category("未知行业")
        
        assert isinstance(result, str)

    def test_get_industry_category_none(self):
        """测试空行业类别"""
        result = get_industry_category(None)
        
        assert isinstance(result, str)

    def test_calculate_industry_score(self):
        """测试行业评分计算"""
        result = calculate_industry_score("银行")
        
        assert isinstance(result, dict)

    def test_calculate_industry_score_unknown(self):
        """测试未知行业评分"""
        result = calculate_industry_score("未知行业")
        
        assert isinstance(result, dict)
