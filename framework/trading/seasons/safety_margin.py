"""动态安全边际模块

核心逻辑:
- 基于 DCF 估值 + 当前价格计算安全边际
- β 系数动态调整阈值
- PE/PB 历史分位辅助判断
- 等级分类: 极度低估 / 低估 / 合理 / 高估 / 极度高估
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from framework.events import Events


class MarginLevel(str, Enum):
    """安全边际等级"""

    DEEPLY_UNDERVALUED = "deeply_undervalued"  # 极度低估
    UNDERVALUED = "undervalued"  # 低估
    FAIR = "fair"  # 合理
    OVERVALUED = "overvalued"  # 高估
    DEEPLY_OVERVALUED = "deeply_overvalued"  # 极度高估


# β 系数对阈值的调整因子
BETA_ADJUSTMENT_RULES: dict[str, tuple[float, float]] = {
    "high_volatility": (1.2, 1.3),  # β > 1.5: 阈值 × 1.2~1.3
    "normal": (1.0, 1.0),  # 0.8 ≤ β ≤ 1.5: 阈值不变
    "low_volatility": (0.8, 0.85),  # β < 0.8: 阈值 × 0.8~0.85
}

# 默认安全边际阈值（基于价值投资的经典标准）
DEFAULT_THRESHOLDS: dict[str, float] = {
    "deeply_undervalued": 0.40,  # 安全边际 ≥ 40%
    "undervalued": 0.20,  # 安全边际 ≥ 20%
    "overvalued": -0.10,  # 安全边际 < -10%
    "deeply_overvalued": -0.20,  # 安全边际 < -20%
}


@dataclass(frozen=True)
class SafetyMarginResult:
    """安全边际计算结果"""

    ts_code: str
    dcf_value: float
    current_price: float
    safety_margin: float  # (dcf - price) / price
    level: MarginLevel
    beta: Optional[float] = None
    beta_adjustment_factor: float = 1.0
    adjusted_thresholds: dict[str, float] = field(default_factory=dict)

    # PE/PB 分位
    pe_percentile: Optional[float] = None
    pb_percentile: Optional[float] = None

    @property
    def margin_pct(self) -> float:
        """安全边际百分比"""
        return self.safety_margin * 100


class SafetyMarginCalculator:
    """动态安全边际计算器

    特性:
    - β 系数动态调整阈值
    - PE/PB 历史分位辅助
    - EventBus 事件通知
    """

    def __init__(
        self,
        thresholds: Optional[dict[str, float]] = None,
    ) -> None:
        self._thresholds = thresholds or DEFAULT_THRESHOLDS.copy()

    def _get_beta_adjustment(self, beta: Optional[float]) -> tuple[float, float]:
        """根据 β 系数获取阈值调整因子"""
        if beta is None:
            return 1.0, 1.0
        if beta > 1.5:
            return BETA_ADJUSTMENT_RULES["high_volatility"]
        if beta < 0.8:
            return BETA_ADJUSTMENT_RULES["low_volatility"]
        return BETA_ADJUSTMENT_RULES["normal"]

    def _adjust_thresholds(self, beta: Optional[float]) -> dict[str, float]:
        """根据 β 系数调整阈值"""
        lower_factor, upper_factor = self._get_beta_adjustment(beta)
        adjusted: dict[str, float] = {}
        for key, value in self._thresholds.items():
            factor = lower_factor if value > 0 else upper_factor
            adjusted[key] = round(value * factor, 4)
        return adjusted

    def calculate_margin(self, dcf_value: float, current_price: float) -> float:
        """计算安全边际

        Returns:
            安全边际比例, 正值=低估, 负值=高估
        """
        if current_price <= 0:
            return 0.0
        return (dcf_value - current_price) / current_price

    def classify_level(
        self,
        safety_margin: float,
        adjusted_thresholds: dict[str, float],
    ) -> MarginLevel:
        """根据安全边际和调整后阈值判断等级"""
        deeply_under = adjusted_thresholds.get("deeply_undervalued", 0.40)
        under = adjusted_thresholds.get("undervalued", 0.20)
        over = adjusted_thresholds.get("overvalued", -0.10)
        deeply_over = adjusted_thresholds.get("deeply_overvalued", -0.20)

        if safety_margin >= deeply_under:
            return MarginLevel.DEEPLY_UNDERVALUED
        if safety_margin >= under:
            return MarginLevel.UNDERVALUED
        if safety_margin >= over:
            return MarginLevel.FAIR
        if safety_margin >= deeply_over:
            return MarginLevel.OVERVALUED
        return MarginLevel.DEEPLY_OVERVALUED

    def calculate(
        self,
        ts_code: str,
        dcf_value: float,
        current_price: float,
        beta: Optional[float] = None,
        pe_percentile: Optional[float] = None,
        pb_percentile: Optional[float] = None,
    ) -> SafetyMarginResult:
        """计算安全边际并分级

        Args:
            ts_code: 股票代码
            dcf_value: DCF 估值
            current_price: 当前价格
            beta: 个股 β 系数
            pe_percentile: PE 历史分位 (0-100)
            pb_percentile: PB 历史分位 (0-100)

        Returns:
            SafetyMarginResult
        """
        safety_margin = self.calculate_margin(dcf_value, current_price)
        adjusted_thresholds = self._adjust_thresholds(beta)
        lower_factor, _ = self._get_beta_adjustment(beta)

        level = self.classify_level(safety_margin, adjusted_thresholds)

        # PE/PB 分位辅助修正：如果分位极端，提升一级
        if pe_percentile is not None and pb_percentile is not None:
            level = self._adjust_by_valuation_percentile(
                level, safety_margin, pe_percentile, pb_percentile, adjusted_thresholds
            )

        result = SafetyMarginResult(
            ts_code=ts_code,
            dcf_value=dcf_value,
            current_price=current_price,
            safety_margin=round(safety_margin, 6),
            level=level,
            beta=beta,
            beta_adjustment_factor=lower_factor,
            adjusted_thresholds=adjusted_thresholds,
            pe_percentile=pe_percentile,
            pb_percentile=pb_percentile,
        )

        # 发送事件
        Events.safety_margin_updated.send(
            sender=self,
            ts_code=ts_code,
            level=level.value,
            margin_pct=result.margin_pct,
        )

        return result

    def _adjust_by_valuation_percentile(
        self,
        current_level: MarginLevel,
        safety_margin: float,
        pe_percentile: float,
        pb_percentile: float,
        thresholds: dict[str, float],
    ) -> MarginLevel:
        """PE/PB 分位极端时修正等级

        规则:
        - PE+PB 都在 10% 以下 → 更低估一级
        - PE+PB 都在 90% 以上 → 更高估一级
        """
        order = list(MarginLevel)
        idx = order.index(current_level)

        if pe_percentile < 10 and pb_percentile < 10 and idx > 0:
            # 双低分位 → 更低估
            return order[idx - 1]
        if pe_percentile > 90 and pb_percentile > 90 and idx < len(order) - 1:
            # 双高分位 → 更高估
            return order[idx + 1]

        return current_level

    @staticmethod
    def calc_pe_percentile(
        pe_series: pd.Series,
        current_pe: float,
    ) -> float:
        """计算 PE 历史分位"""
        if pe_series.empty:
            return 50.0
        return float((pe_series < current_pe).sum() / len(pe_series) * 100)

    @staticmethod
    def calc_pb_percentile(
        pb_series: pd.Series,
        current_pb: float,
    ) -> float:
        """计算 PB 历史分位"""
        if pb_series.empty:
            return 50.0
        return float((pb_series < current_pb).sum() / len(pb_series) * 100)
