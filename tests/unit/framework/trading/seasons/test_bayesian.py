"""贝叶斯转换引擎单元测试

测试目标:
- 先验分布
- 似然函数
- 后验概率计算
- 动作建议
"""

import numpy as np
import pytest

from framework.trading.wuxing.bayesian import (
    LIKELIHOOD_PARAMS,
    PRIORS,
    ActionAdvice,
    BayesianResult,
    BayesianTransitionEngine,
)
from framework.trading.wuxing.detectors import DetectionResult, WuxingElement


class TestPriors:
    """先验分布测试"""

    def test_priors_sum_to_less_than_one(self) -> None:
        """测试先验概率合理"""
        # 每个 from_state 的先验之和应 ≤ 1
        from_states = ["wood", "fire", "metal", "water", "soil"]
        for fs in from_states:
            related = [v for k, v in PRIORS.items() if k.startswith(f"{fs}_to_")]
            assert sum(related) <= 1.0 or len(related) == 0

    def test_wood_to_soil_highest(self) -> None:
        """测试木→土概率最高"""
        assert PRIORS["wood_to_soil"] > PRIORS["wood_to_fire"]

    def test_soil_uniform(self) -> None:
        """测试土→各状态均匀分布"""
        soil_priors = [v for k, v in PRIORS.items() if k.startswith("soil_to_")]
        assert len(set(soil_priors)) == 1  # 全部相等


class TestLikelihood:
    """似然函数测试"""

    def test_likelihood_params_exist(self) -> None:
        """测试所有状态都有似然参数"""
        for state in ["wood", "fire", "metal", "water", "soil"]:
            assert state in LIKELIHOOD_PARAMS

    def test_likelihood_calculation(self) -> None:
        """测试似然计算"""
        engine = BayesianTransitionEngine()
        observations = {"pullback": -0.35, "volume_ratio": 2.5}

        likelihood = engine._calc_likelihood(WuxingElement.WOOD, observations)
        # 归一化后应在 [0, 1] 之间
        assert 0.0 < likelihood <= 1.0


class TestBayesianInference:
    """贝叶斯推断测试"""

    def test_infer_wood_state(self) -> None:
        """测试木状态推断"""
        engine = BayesianTransitionEngine()

        detection = DetectionResult(
            element=WuxingElement.WOOD,
            confidence=0.8,
            reasons=["回撤30%", "放量2.5倍"],
            raw_scores={
                "pullback": -0.35,
                "volume_ratio": 2.5,
                "ema_convergence": 0.03,
            },
        )

        result = engine.infer(WuxingElement.WOOD, detection)

        assert isinstance(result, BayesianResult)
        assert result.current_state == WuxingElement.WOOD
        assert len(result.posterior_probs) == 5  # 5个状态
        assert sum(result.posterior_probs.values()) == pytest.approx(1.0, abs=0.01)
        assert result.next_prob > 0

    def test_infer_posterior_probs_normalized(self) -> None:
        """测试后验概率归一化"""
        engine = BayesianTransitionEngine()

        detection = DetectionResult(
            element=WuxingElement.FIRE,
            confidence=0.7,
            raw_scores={"breakout_pct": 0.30, "volume_ratio": 4.0},
        )

        result = engine.infer(WuxingElement.FIRE, detection)
        total = sum(result.posterior_probs.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_infer_most_likely_next(self) -> None:
        """测试最可能的下一个状态"""
        engine = BayesianTransitionEngine()

        # 使用木状态的观测，但当前状态也是木
        # 由于观测匹配木状态，自转换概率可能最高
        detection = DetectionResult(
            element=WuxingElement.WOOD,
            confidence=0.8,
            raw_scores={"pullback": -0.35, "volume_ratio": 2.5},
        )

        result = engine.infer(WuxingElement.WOOD, detection)
        # 观测匹配当前状态 → 自转换概率高，或者转向土（先验高）
        # 断言最可能的状态是木或土之一
        assert result.most_likely_next in [WuxingElement.WOOD, WuxingElement.SOIL]
        assert result.next_prob > 0.3


class TestActionAdvice:
    """动作建议测试"""

    def test_wood_to_fire_add(self) -> None:
        """测试木→火建议加仓"""
        engine = BayesianTransitionEngine()
        action = engine._suggest_action(WuxingElement.WOOD, WuxingElement.FIRE, 0.8)
        assert action == ActionAdvice.ADD

    def test_fire_to_metal_reduce(self) -> None:
        """测试火→金建议减仓"""
        engine = BayesianTransitionEngine()
        action = engine._suggest_action(WuxingElement.FIRE, WuxingElement.METAL, 0.8)
        assert action == ActionAdvice.REDUCE

    def test_metal_to_water_stop_loss(self) -> None:
        """测试金→水建议止损"""
        engine = BayesianTransitionEngine()
        action = engine._suggest_action(WuxingElement.METAL, WuxingElement.WATER, 0.8)
        assert action == ActionAdvice.STOP_LOSS

    def test_low_prob_downgrade_to_wait(self) -> None:
        """测试低概率降级为等待"""
        engine = BayesianTransitionEngine()
        action = engine._suggest_action(WuxingElement.FIRE, WuxingElement.METAL, 0.3)
        # 概率 < 0.5，减仓降级为等待
        assert action == ActionAdvice.WAIT

    def test_soil_to_any_probe_or_wait(self) -> None:
        """测试土状态建议试探或等待"""
        engine = BayesianTransitionEngine()

        action_wood = engine._suggest_action(
            WuxingElement.SOIL, WuxingElement.WOOD, 0.8
        )
        assert action_wood == ActionAdvice.PROBE

        action_metal = engine._suggest_action(
            WuxingElement.SOIL, WuxingElement.METAL, 0.8
        )
        assert action_metal == ActionAdvice.WAIT


class TestConfidenceCalculation:
    """置信度计算测试"""

    def test_high_confidence_concentrated(self) -> None:
        """测试分布集中 → 高置信度"""
        engine = BayesianTransitionEngine()
        posteriors = {
            WuxingElement.WOOD: 0.8,
            WuxingElement.SOIL: 0.1,
            WuxingElement.FIRE: 0.05,
            WuxingElement.METAL: 0.03,
            WuxingElement.WATER: 0.02,
        }
        confidence = engine._calc_confidence(posteriors, 0.8)
        # 分布集中，置信度应较高
        assert confidence >= 0.5

    def test_low_confidence_uniform(self) -> None:
        """测试分布均匀 → 低置信度"""
        engine = BayesianTransitionEngine()
        posteriors = {
            WuxingElement.WOOD: 0.2,
            WuxingElement.SOIL: 0.2,
            WuxingElement.FIRE: 0.2,
            WuxingElement.METAL: 0.2,
            WuxingElement.WATER: 0.2,
        }
        confidence = engine._calc_confidence(posteriors, 0.2)
        assert confidence < 0.5


class TestBayesianResult:
    """BayesianResult 数据模型测试"""

    def test_transition_matrix(self) -> None:
        """测试转换矩阵"""
        result = BayesianResult(
            current_state=WuxingElement.WOOD,
            posterior_probs={
                WuxingElement.SOIL: 0.7,
                WuxingElement.FIRE: 0.3,
            },
            most_likely_next=WuxingElement.SOIL,
            next_prob=0.7,
            action=ActionAdvice.PROBE,
            confidence=0.8,
        )

        matrix = result.transition_matrix
        assert "wood_to_soil" in matrix
        assert "wood_to_fire" in matrix
        assert matrix["wood_to_soil"] == 0.7
