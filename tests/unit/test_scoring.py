"""
评分系统单元测试
"""

import pytest

from app.analysis.scoring import (
    ScoringEngine,
    score_to_rating,
)


class TestScoringEngine:
    """评分引擎测试"""

    def test_calculate_long_term_score(self):
        """测试长线评分计算"""
        score = ScoringEngine.calculate_long_term_score(
            company_score=80,
            industry_score=70,
            market_score=60,
            policy_score=75,
            trend_score=85,
        )

        # 验证评分在合理范围
        assert 0 <= score <= 100

        # 验证权重计算正确
        # 80*0.25 + 70*0.1875 + 60*0.125 + 75*0.0625 + 85*0.375
        expected = 80 * 0.25 + 70 * 0.1875 + 60 * 0.125 + 75 * 0.0625 + 85 * 0.375
        assert abs(score - expected) < 0.01

    def test_calculate_short_term_score(self):
        """测试短线评分计算"""
        score = ScoringEngine.calculate_short_term_score(
            momentum_score=70,
            volume_score=60,
            trend_score=80,
            volatility_score=50,
        )

        assert 0 <= score <= 100

    def test_calculate_signal_strength(self):
        """测试信号强度计算"""
        # 高分值场景
        strength = ScoringEngine.calculate_signal_strength(
            trend_score=80,
            volume_score=75,
            momentum_score=70,
        )
        assert 0 <= strength <= 5

        # 低分值场景
        strength_low = ScoringEngine.calculate_signal_strength(
            trend_score=30,
            volume_score=35,
            momentum_score=40,
        )
        assert 0 <= strength_low <= 5
        assert strength > strength_low

    def test_calculate_opportunity_quality(self):
        """测试机会质量计算"""
        # 低位+上涨趋势+超卖 = 高机会质量
        quality = ScoringEngine.calculate_opportunity_quality(
            price_position=0.2,
            trend_direction=1,
            rsi=25,
        )
        assert quality >= 3  # 应该是较高分数

        # 高位+下跌趋势 = 低机会质量
        quality_low = ScoringEngine.calculate_opportunity_quality(
            price_position=0.9,
            trend_direction=-1,
            rsi=75,
        )
        assert quality_low < quality

    def test_calculate_risk_level(self):
        """测试风险等级计算"""
        # 低波动+低负债+低价位 = 低风险
        risk = ScoringEngine.calculate_risk_level(
            volatility=0.15,
            debt_ratio=30,
            price_position=0.3,
        )
        assert 1 <= risk <= 3  # 应该是较低风险

        # 高波动+高负债+高价位 = 高风险
        risk_high = ScoringEngine.calculate_risk_level(
            volatility=0.6,
            debt_ratio=85,
            price_position=0.9,
        )
        assert risk_high >= 3  # 应该是较高风险

    def test_get_recommendation(self):
        """测试投资建议"""
        # 高分 → 买入
        rec, conf = ScoringEngine.get_recommendation(85)
        assert rec == "强烈买入"
        assert conf == 90

        # 中分 → 持有
        rec, conf = ScoringEngine.get_recommendation(60)
        assert rec == "持有"
        assert conf == 60

        # 低分 → 卖出
        rec, conf = ScoringEngine.get_recommendation(30)
        assert rec == "卖出"
        assert conf == 30


class TestScoreToRating:
    """分数转评级测试"""

    def test_rating_conversion(self):
        """测试评级转换"""
        assert score_to_rating(85) == "A"
        assert score_to_rating(70) == "B"
        assert score_to_rating(55) == "C"
        assert score_to_rating(40) == "D"
        assert score_to_rating(25) == "E"

    def test_boundary_values(self):
        """测试边界值"""
        assert score_to_rating(80) == "A"
        assert score_to_rating(79.9) == "B"
        assert score_to_rating(65) == "B"
        assert score_to_rating(64.9) == "C"
