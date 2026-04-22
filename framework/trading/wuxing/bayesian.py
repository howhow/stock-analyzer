"""贝叶斯转换引擎

核心逻辑:
- 先验分布: 专家经验 + 历史统计
- 似然函数: 当前观测数据匹配各状态的概率
- 后验概率: P(状态|观测) = P(观测|状态) × P(状态) / P(观测)
- 动作建议: 基于后验概率生成操作建议

先验来源:
- 专家经验: 冯柳/段永平/张磊投资体系中的形态识别经验
- 历史统计: A股2015-2025年历史回测统计
- 动态修正: 每季度根据实盘表现调整先验
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from framework.trading.wuxing.detectors import WuxingElement, DetectionResult


# ═══════════════════════════════════════════════════════════════
# 先验分布配置
# ═══════════════════════════════════════════════════════════════

# 五行转换先验概率（基于历史统计 + 专家经验）
# 格式: {from_state}_{to_state}: probability
PRIORS: dict[str, float] = {
    # 木 → 其他
    "wood_to_soil": 0.70,  # 木最可能转入土（过渡）
    "wood_to_fire": 0.30,  # 木也可能直接转火（强势突破）
    # 火 → 其他
    "fire_to_soil": 0.60,
    "fire_to_metal": 0.40,  # 火可能直接转金（顶部形成）
    # 金 → 其他
    "metal_to_soil": 0.70,
    "metal_to_water": 0.30,
    # 水 → 其他
    "water_to_soil": 0.60,
    "water_to_wood": 0.40,  # 水可能直接转木（底部形成）
    # 土 → 其他（土是过渡态，向各状态转换）
    "soil_to_wood": 0.25,
    "soil_to_fire": 0.25,
    "soil_to_metal": 0.25,
    "soil_to_water": 0.25,
}

# 似然函数参数: {state: {indicator: (mean, std)}}
# 基于历史数据统计各状态下指标的分布
LIKELIHOOD_PARAMS: dict[str, dict[str, tuple[float, float]]] = {
    "wood": {
        "pullback": (-0.35, 0.10),  # 回撤均值 -35%，标准差 10%
        "volume_ratio": (2.5, 0.5),  # 放量均值 2.5 倍
        "ema_convergence": (0.03, 0.02),  # EMA 收敛
    },
    "fire": {
        "breakout_pct": (0.30, 0.10),  # 突破幅度
        "volume_ratio": (4.0, 1.0),  # 放量
        "ema_distance": (0.05, 0.03),  # 距 EMA 距离
    },
    "metal": {
        "daily_change": (-0.06, 0.03),  # 日跌幅
        "volume_ratio": (2.0, 0.8),  # 放量跌
        "fib_retracement": (0.382, 0.05),  # 斐波那契回落
    },
    "water": {
        "total_drop": (-0.07, 0.02),  # 累计跌幅
        "volume_ratio": (0.40, 0.15),  # 缩量
    },
    "soil": {
        "volatility": (0.02, 0.01),  # 低波动
        "volume_ratio": (1.0, 0.3),  # 正常成交量
    },
}


class ActionAdvice(str, Enum):
    """动作建议"""

    WAIT = "wait"  # 等待
    PROBE = "probe"  # 试探
    ADD = "add"  # 加仓
    REDUCE = "reduce"  # 减仓
    STOP_LOSS = "stop_loss"  # 止损
    HOLD = "hold"  # 持有


@dataclass(frozen=True)
class BayesianResult:
    """贝叶斯推断结果"""

    current_state: WuxingElement
    posterior_probs: dict[WuxingElement, float]
    most_likely_next: WuxingElement
    next_prob: float
    action: ActionAdvice
    confidence: float

    @property
    def transition_matrix(self) -> dict[str, float]:
        """转换概率矩阵"""
        return {
            f"{self.current_state.value}_to_{target.value}": prob
            for target, prob in self.posterior_probs.items()
        }


class BayesianTransitionEngine:
    """贝叶斯转换引擎

    特性:
    - 先验分布可配置
    - 似然函数基于历史统计
    - 后验概率动态计算
    - 动作建议基于后验
    """

    def __init__(
        self,
        priors: Optional[dict[str, float]] = None,
        likelihood_params: Optional[dict[str, dict[str, tuple[float, float]]]] = None,
    ) -> None:
        self._priors = priors or PRIORS.copy()
        self._likelihood_params = likelihood_params or LIKELIHOOD_PARAMS.copy()

    def _get_prior(self, from_state: WuxingElement, to_state: WuxingElement) -> float:
        """获取先验概率"""
        key = f"{from_state.value}_to_{to_state.value}"
        return self._priors.get(key, 0.10)  # 默认 10%

    def _calc_likelihood(
        self,
        state: WuxingElement,
        observations: dict[str, float],
    ) -> float:
        """计算似然 P(观测|状态)

        使用高斯分布假设，但归一化到 [0, 1]:
        likelihood = exp(-0.5 * Σ((x-μ)/σ)²)
        """
        params = self._likelihood_params.get(state.value, {})
        if not params:
            return 0.5

        sum_sq = 0.0
        count = 0
        for indicator, (mean, std) in params.items():
            if indicator in observations and std > 0:
                x = observations[indicator]
                sum_sq += ((x - mean) / std) ** 2
                count += 1

        if count == 0:
            return 0.5

        # 归一化似然: exp(-0.5 * 平均标准化距离²)
        avg_sq = sum_sq / count
        likelihood = np.exp(-0.5 * avg_sq)

        return float(np.clip(likelihood, 0.01, 1.0))

    def infer(
        self,
        current_state: WuxingElement,
        detection_result: DetectionResult,
    ) -> BayesianResult:
        """贝叶斯推断

        Args:
            current_state: 当前五行状态
            detection_result: 识别器结果（含原始观测值）

        Returns:
            BayesianResult
        """
        observations = detection_result.raw_scores

        # 所有可能的目标状态
        all_states = list(WuxingElement)

        # 计算未归一化的后验
        posteriors: dict[WuxingElement, float] = {}
        for target_state in all_states:
            prior = self._get_prior(current_state, target_state)
            likelihood = self._calc_likelihood(target_state, observations)
            posteriors[target_state] = prior * likelihood

        # 归一化
        total = sum(posteriors.values())
        if total > 0:
            posteriors = {k: v / total for k, v in posteriors.items()}

        # 最可能的下一个状态
        most_likely = max(posteriors, key=posteriors.get)
        next_prob = posteriors[most_likely]

        # 动作建议
        action = self._suggest_action(current_state, most_likely, next_prob)

        # 置信度
        confidence = self._calc_confidence(posteriors, next_prob)

        return BayesianResult(
            current_state=current_state,
            posterior_probs=posteriors,
            most_likely_next=most_likely,
            next_prob=next_prob,
            action=action,
            confidence=confidence,
        )

    def _suggest_action(
        self,
        current: WuxingElement,
        most_likely: WuxingElement,
        prob: float,
    ) -> ActionAdvice:
        """基于状态转换建议动作"""
        # 转换矩阵 → 动作映射
        action_map: dict[tuple[WuxingElement, WuxingElement], ActionAdvice] = {
            # 木 → 火: 加仓
            (WuxingElement.WOOD, WuxingElement.FIRE): ActionAdvice.ADD,
            # 木 → 土: 试探
            (WuxingElement.WOOD, WuxingElement.SOIL): ActionAdvice.PROBE,
            # 火 → 金: 减仓
            (WuxingElement.FIRE, WuxingElement.METAL): ActionAdvice.REDUCE,
            # 火 → 土: 持有
            (WuxingElement.FIRE, WuxingElement.SOIL): ActionAdvice.HOLD,
            # 金 → 水: 止损
            (WuxingElement.METAL, WuxingElement.WATER): ActionAdvice.STOP_LOSS,
            # 金 → 土: 减仓
            (WuxingElement.METAL, WuxingElement.SOIL): ActionAdvice.REDUCE,
            # 水 → 木: 试探（底部）
            (WuxingElement.WATER, WuxingElement.WOOD): ActionAdvice.PROBE,
            # 水 → 土: 等待
            (WuxingElement.WATER, WuxingElement.SOIL): ActionAdvice.WAIT,
            # 土 → 任何: 等待/试探
            (WuxingElement.SOIL, WuxingElement.WOOD): ActionAdvice.PROBE,
            (WuxingElement.SOIL, WuxingElement.FIRE): ActionAdvice.PROBE,
            (WuxingElement.SOIL, WuxingElement.METAL): ActionAdvice.WAIT,
            (WuxingElement.SOIL, WuxingElement.WATER): ActionAdvice.WAIT,
        }

        action = action_map.get((current, most_likely), ActionAdvice.WAIT)

        # 如果概率不够高，降级为等待
        if prob < 0.5:
            if action in (ActionAdvice.ADD, ActionAdvice.REDUCE, ActionAdvice.STOP_LOSS):
                return ActionAdvice.WAIT

        return action

    def _calc_confidence(
        self,
        posteriors: dict[WuxingElement, float],
        max_prob: float,
    ) -> float:
        """计算推断置信度"""
        # 熵越低（分布越集中），置信度越高
        entropy = -sum(p * np.log(p + 1e-10) for p in posteriors.values())
        max_entropy = np.log(len(posteriors))

        # 归一化熵 → 置信度
        if max_entropy > 0:
            entropy_ratio = entropy / max_entropy
            confidence = 1.0 - entropy_ratio
        else:
            confidence = 1.0

        # 结合最大概率
        confidence = 0.6 * confidence + 0.4 * max_prob

        return round(float(confidence), 2)
