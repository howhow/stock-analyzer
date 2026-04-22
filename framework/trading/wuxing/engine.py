"""五行引擎 — 战术层

五行系统: 基于量价驱动的短线波段识别
- 木(wood): 底部蓄力 → 试探建仓
- 火(fire): 上涨确认 → 加仓
- 金(metal): 顶部形成 → 减仓
- 水(water): 回落收敛 → 清仓
- 土(soil): 过渡态 → 贝叶斯推断

五行循环期间，四季长线仓位绝对不动。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from framework.events import Events
from framework.trading.wuxing.bayesian import (
    ActionAdvice,
    BayesianResult,
    BayesianTransitionEngine,
)
from framework.trading.wuxing.detectors import (
    DetectionResult,
    FireStateDetector,
    MetalStateDetector,
    WaterStateDetector,
    WoodStateDetector,
    WuxingElement,
)


@dataclass(frozen=True)
class WuxingState:
    """五行状态数据模型"""

    ts_code: str
    element: WuxingElement
    confidence: float
    detection_result: DetectionResult
    bayesian_result: Optional[BayesianResult] = None
    action: Optional[ActionAdvice] = None

    @property
    def position_guidance(self) -> str:
        """仓位指导"""
        guidance_map: dict[WuxingElement, str] = {
            WuxingElement.WOOD: "试探建仓 10-30%",
            WuxingElement.FIRE: "加仓（=试探量）",
            WuxingElement.METAL: "减五行仓位",
            WuxingElement.WATER: "清五行仓位",
            WuxingElement.SOIL: "等待/试探/止损",
        }
        return guidance_map.get(self.element, "观望")


class WuxingEngine:
    """五行引擎 — 量价驱动，识别当前形态

    特性:
    - 多识别器并行检测
    - 贝叶斯推断转换概率
    - EventBus 事件通知
    - 所有参数用户可配
    """

    def __init__(
        self,
        wood_detector: Optional[WoodStateDetector] = None,
        fire_detector: Optional[FireStateDetector] = None,
        metal_detector: Optional[MetalStateDetector] = None,
        water_detector: Optional[WaterStateDetector] = None,
        bayesian_engine: Optional[BayesianTransitionEngine] = None,
    ) -> None:
        self._wood = wood_detector or WoodStateDetector()
        self._fire = fire_detector or FireStateDetector()
        self._metal = metal_detector or MetalStateDetector()
        self._water = water_detector or WaterStateDetector()
        self._bayesian = bayesian_engine or BayesianTransitionEngine()
        self._current_states: dict[str, WuxingState] = {}

    def analyze(
        self,
        ts_code: str,
        df: pd.DataFrame,
        current_price: float,
        historical_high: float,
        recent_low: float,
        recent_high: float,
        avg_volume_20d: float,
        current_volume: float,
        daily_change: float,
        price_n_days_ago: float,
    ) -> WuxingState:
        """分析股票当前五行状态

        Args:
            ts_code: 股票代码
            df: 日线数据
            current_price: 当前价格
            historical_high: 历史高点
            recent_low: 近期低点
            recent_high: 近期高点
            avg_volume_20d: 20日均量
            current_volume: 当前成交量
            daily_change: 日涨跌幅
            price_n_days_ago: N天前价格

        Returns:
            WuxingState
        """
        # 并行检测所有形态
        detections: list[DetectionResult] = [
            self._wood.detect(
                df, current_price, historical_high, avg_volume_20d, current_volume
            ),
            self._fire.detect(
                df, current_price, recent_low, avg_volume_20d, current_volume
            ),
            self._metal.detect(
                df,
                current_price,
                recent_high,
                recent_low,
                avg_volume_20d,
                current_volume,
                daily_change,
            ),
            self._water.detect(
                df, current_price, price_n_days_ago, avg_volume_20d, current_volume
            ),
        ]

        # 选择置信度最高的形态
        best_detection = max(detections, key=lambda d: d.confidence)

        # 如果置信度太低，判定为土（过渡态）
        if best_detection.confidence < 0.5:
            best_detection = DetectionResult(
                element=WuxingElement.SOIL,
                confidence=0.5,
                reasons=["无明显形态特征，判定为过渡态"],
            )

        # 贝叶斯推断
        current_element = best_detection.element
        bayesian_result = self._bayesian.infer(current_element, best_detection)

        # 创建状态
        state = WuxingState(
            ts_code=ts_code,
            element=current_element,
            confidence=best_detection.confidence,
            detection_result=best_detection,
            bayesian_result=bayesian_result,
            action=bayesian_result.action,
        )

        # 获取上一状态
        previous = self._current_states.get(ts_code)
        if previous is not None and previous.element != current_element:
            Events.wuxing_state_changed.send(
                self,
                ts_code=ts_code,
                old_element=previous.element.value,
                new_element=current_element.value,
                confidence=best_detection.confidence,
                action=bayesian_result.action.value if bayesian_result.action else None,
            )

            # 如果转换概率高，发送 transition_detected 事件
            if bayesian_result.next_prob > 0.7:
                Events.transition_detected.send(
                    self,
                    ts_code=ts_code,
                    from_element=current_element.value,
                    to_element=bayesian_result.most_likely_next.value,
                    probability=bayesian_result.next_prob,
                )

        self._current_states[ts_code] = state
        return state

    def get_current_state(self, ts_code: str) -> Optional[WuxingState]:
        """获取股票当前五行状态"""
        return self._current_states.get(ts_code)
