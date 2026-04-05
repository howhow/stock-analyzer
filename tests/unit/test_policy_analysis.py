"""Policy Analysis完整测试 - 类型安全、防御性编程"""

import pytest

from app.analysis.fundamental.policy import (
    get_policy_sensitivity,
    calculate_policy_score,
)


class TestPolicyAnalysis:
    """政策分析测试"""

    def test_get_policy_sensitivity_known(self):
        """测试已知行业政策敏感度"""
        result = get_policy_sensitivity("银行")

        assert isinstance(result, str)

    def test_get_policy_sensitivity_unknown(self):
        """测试未知行业政策敏感度"""
        result = get_policy_sensitivity("未知行业")

        assert isinstance(result, str)

    def test_get_policy_sensitivity_none(self):
        """测试空行业政策敏感度"""
        result = get_policy_sensitivity(None)

        assert isinstance(result, str)

    def test_calculate_policy_score(self):
        """测试政策评分计算"""
        result = calculate_policy_score("银行")

        assert isinstance(result, dict)

    def test_calculate_policy_score_unknown(self):
        """测试未知行业政策评分"""
        result = calculate_policy_score("未知行业")

        assert isinstance(result, dict)
