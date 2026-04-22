"""五行识别器

五行状态识别逻辑:
- 木(wood): 底部蓄力 — 距历史高点-30% + EMA收敛 + 放量2-3倍
- 火(fire): 上涨确认 — 突破EMA120 + 放量3-5倍 + 突破20%
- 金(metal): 顶部形成 — 放量跌>5% 或 斐波那契0.618回落
- 水(water): 回落收敛 — 连续跌5-10% + 缩量50%
- 土(soil): 过渡态 — 贝叶斯推断转换概率

所有识别器返回 DetectionResult，包含置信度 + 理由
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class WuxingElement(str, Enum):
    """五行元素枚举"""

    WOOD = "wood"  # 木 — 底部蓄力
    FIRE = "fire"  # 火 — 上涨确认
    METAL = "metal"  # 金 — 顶部形成
    WATER = "water"  # 水 — 回落收敛
    SOIL = "soil"  # 土 — 过渡态


@dataclass(frozen=True)
class DetectionResult:
    """识别结果"""

    element: WuxingElement
    confidence: float  # 0.0 ~ 1.0
    reasons: list[str] = field(default_factory=list)
    raw_scores: dict[str, float] = field(default_factory=dict)

    @property
    def is_confident(self) -> bool:
        """是否高置信度（>0.7）"""
        return self.confidence >= 0.7


class WoodStateDetector:
    """木形态识别器 — 底部蓄力

    核心条件:
    - 距历史高点 -30% 以上（深度回调）
    - EMA 收敛（短期 EMA 靠近长期 EMA）
    - 放量 2-3 倍（底部放量吸筹）
    """

    def __init__(
        self,
        pullback_threshold: float = -0.30,
        ema_convergence_threshold: float = 0.05,
        volume_multiplier_min: float = 2.0,
        volume_multiplier_max: float = 3.0,
    ) -> None:
        self._pullback_threshold = pullback_threshold
        self._ema_convergence_threshold = ema_convergence_threshold
        self._volume_min = volume_multiplier_min
        self._volume_max = volume_multiplier_max

    def detect(
        self,
        df: pd.DataFrame,
        current_price: float,
        historical_high: float,
        avg_volume_20d: float,
        current_volume: float,
    ) -> DetectionResult:
        """识别木形态

        Args:
            df: 日线数据（需包含 close, volume 列）
            current_price: 当前价格
            historical_high: 历史高点
            avg_volume_20d: 20日均量
            current_volume: 当前成交量

        Returns:
            DetectionResult
        """
        reasons: list[str] = []
        raw_scores: dict[str, float] = {}

        # 1. 距历史高点回撤
        pullback = (current_price - historical_high) / historical_high
        raw_scores["pullback"] = pullback
        if pullback <= self._pullback_threshold:
            reasons.append(
                f"距高点回撤 {pullback*100:.1f}% ≥ {abs(self._pullback_threshold)*100:.0f}%"
            )

        # 2. EMA 收敛
        if len(df) >= 60:
            ema12 = df["close"].ewm(span=12).mean().iloc[-1]
            ema26 = df["close"].ewm(span=26).mean().iloc[-1]
            ema_convergence = abs(ema12 - ema26) / ema26
            raw_scores["ema_convergence"] = ema_convergence
            if ema_convergence <= self._ema_convergence_threshold:
                reasons.append(
                    f"EMA 收敛 {ema_convergence*100:.1f}%"
                    f" ≤ {self._ema_convergence_threshold*100:.0f}%"
                )

        # 3. 放量
        if avg_volume_20d > 0:
            volume_ratio = current_volume / avg_volume_20d
            raw_scores["volume_ratio"] = volume_ratio
            if self._volume_min <= volume_ratio <= self._volume_max:
                reasons.append(
                    f"放量 {volume_ratio:.1f} 倍"
                    f"（{self._volume_min:.0f}~{self._volume_max:.0f}倍区间）"
                )

        # 计算置信度
        confidence = self._calc_confidence(reasons, raw_scores)

        return DetectionResult(
            element=WuxingElement.WOOD,
            confidence=confidence,
            reasons=reasons,
            raw_scores=raw_scores,
        )

    def _calc_confidence(
        self,
        reasons: list[str],
        raw_scores: dict[str, float],
    ) -> float:
        """计算置信度

        基础分: 0.3
        每个条件满足 +0.2
        额外加分: 条件越极端，加分越多
        """
        base = 0.3
        bonus = len(reasons) * 0.2

        # 额外加分
        extra = 0.0
        if "pullback" in raw_scores:
            pullback = raw_scores["pullback"]
            if pullback <= -0.40:
                extra += 0.1
        if "volume_ratio" in raw_scores:
            vr = raw_scores["volume_ratio"]
            if vr >= 2.5:
                extra += 0.1

        return min(base + bonus + extra, 1.0)


class FireStateDetector:
    """火形态识别器 — 上涨确认

    核心条件:
    - 突破 EMA120（站上长期均线）
    - 放量 3-5 倍（突破放量）
    - 突破幅度 ≥ 20%（从底部起算）
    """

    def __init__(
        self,
        ema_period: int = 120,
        volume_multiplier_min: float = 3.0,
        volume_multiplier_max: float = 5.0,
        breakout_threshold: float = 0.20,
    ) -> None:
        self._ema_period = ema_period
        self._volume_min = volume_multiplier_min
        self._volume_max = volume_multiplier_max
        self._breakout_threshold = breakout_threshold

    def detect(
        self,
        df: pd.DataFrame,
        current_price: float,
        recent_low: float,
        avg_volume_20d: float,
        current_volume: float,
    ) -> DetectionResult:
        """识别火形态"""
        reasons: list[str] = []
        raw_scores: dict[str, float] = {}

        # 1. 突破 EMA120
        if len(df) >= self._ema_period:
            ema120 = df["close"].ewm(span=self._ema_period).mean().iloc[-1]
            raw_scores["ema120"] = ema120
            if current_price > ema120:
                reasons.append(f"突破 EMA{self._ema_period} ({ema120:.2f})")

        # 2. 放量
        if avg_volume_20d > 0:
            volume_ratio = current_volume / avg_volume_20d
            raw_scores["volume_ratio"] = volume_ratio
            if self._volume_min <= volume_ratio <= self._volume_max:
                reasons.append(f"放量 {volume_ratio:.1f} 倍")

        # 3. 突破幅度
        if recent_low > 0:
            breakout_pct = (current_price - recent_low) / recent_low
            raw_scores["breakout_pct"] = breakout_pct
            if breakout_pct >= self._breakout_threshold:
                reasons.append(
                    f"突破幅度 {breakout_pct*100:.1f}%"
                    f" ≥ {self._breakout_threshold*100:.0f}%"
                )

        confidence = self._calc_confidence(reasons, raw_scores)

        return DetectionResult(
            element=WuxingElement.FIRE,
            confidence=confidence,
            reasons=reasons,
            raw_scores=raw_scores,
        )

    def _calc_confidence(
        self,
        reasons: list[str],
        raw_scores: dict[str, float],
    ) -> float:
        """计算置信度"""
        base = 0.3
        bonus = len(reasons) * 0.2

        extra = 0.0
        if "breakout_pct" in raw_scores:
            bp = raw_scores["breakout_pct"]
            if bp >= 0.30:
                extra += 0.1
        if "volume_ratio" in raw_scores:
            vr = raw_scores["volume_ratio"]
            if vr >= 4.0:
                extra += 0.1

        return min(base + bonus + extra, 1.0)


class MetalStateDetector:
    """金形态识别器 — 顶部形成

    核心条件:
    - 放量跌 > 5%（放量下跌）
    - 或斐波那契 0.618 回落（从高点回落 38.2%）
    """

    def __init__(
        self,
        drop_threshold: float = -0.05,
        fibonacci_level: float = 0.618,
    ) -> None:
        self._drop_threshold = drop_threshold
        self._fibonacci_level = fibonacci_level

    def detect(
        self,
        df: pd.DataFrame,
        current_price: float,
        recent_high: float,
        recent_low: float,
        avg_volume_20d: float,
        current_volume: float,
        daily_change: float,
    ) -> DetectionResult:
        """识别金形态"""
        reasons: list[str] = []
        raw_scores: dict[str, float] = {}

        # 1. 放量跌 > 5%
        if avg_volume_20d > 0:
            volume_ratio = current_volume / avg_volume_20d
            raw_scores["volume_ratio"] = volume_ratio

        raw_scores["daily_change"] = daily_change
        if daily_change <= self._drop_threshold and volume_ratio >= 1.5:
            reasons.append(
                f"放量跌 {daily_change*100:.1f}%（量 {volume_ratio:.1f} 倍）"
            )

        # 2. 斐波那契 0.618 回落
        if recent_high > recent_low:
            fib_retracement = (recent_high - current_price) / (recent_high - recent_low)
            raw_scores["fib_retracement"] = fib_retracement
            if abs(fib_retracement - (1 - self._fibonacci_level)) <= 0.05:
                reasons.append(f"斐波那契 0.618 回落 ({fib_retracement*100:.1f}%)")

        confidence = self._calc_confidence(reasons, raw_scores)

        return DetectionResult(
            element=WuxingElement.METAL,
            confidence=confidence,
            reasons=reasons,
            raw_scores=raw_scores,
        )

    def _calc_confidence(
        self,
        reasons: list[str],
        raw_scores: dict[str, float],
    ) -> float:
        """计算置信度"""
        base = 0.3
        bonus = len(reasons) * 0.25

        extra = 0.0
        if "daily_change" in raw_scores:
            dc = raw_scores["daily_change"]
            if dc <= -0.08:
                extra += 0.1

        return min(base + bonus + extra, 1.0)


class WaterStateDetector:
    """水形态识别器 — 回落收敛

    核心条件:
    - 连续跌 5-10%（3-5 个交易日）
    - 缩量 50%（成交量萎缩）
    """

    def __init__(
        self,
        consecutive_drop_min: float = -0.05,
        consecutive_drop_max: float = -0.10,
        volume_shrink_threshold: float = 0.50,
        lookback_days: int = 5,
    ) -> None:
        self._drop_min = consecutive_drop_min
        self._drop_max = consecutive_drop_max
        self._volume_shrink = volume_shrink_threshold
        self._lookback = lookback_days

    def detect(
        self,
        df: pd.DataFrame,
        current_price: float,
        price_n_days_ago: float,
        avg_volume_20d: float,
        current_volume: float,
    ) -> DetectionResult:
        """识别水形态"""
        reasons: list[str] = []
        raw_scores: dict[str, float] = {}

        # 1. 连续跌幅
        if price_n_days_ago > 0:
            total_drop = (current_price - price_n_days_ago) / price_n_days_ago
            raw_scores["total_drop"] = total_drop
            if self._drop_min >= total_drop >= self._drop_max:
                reasons.append(f"{self._lookback}日跌幅 {total_drop*100:.1f}%")

        # 2. 缩量
        if avg_volume_20d > 0:
            volume_ratio = current_volume / avg_volume_20d
            raw_scores["volume_ratio"] = volume_ratio
            if volume_ratio <= self._volume_shrink:
                reasons.append(
                    f"缩量至 {volume_ratio*100:.0f}%（≤{self._volume_shrink*100:.0f}%）"
                )

        confidence = self._calc_confidence(reasons, raw_scores)

        return DetectionResult(
            element=WuxingElement.WATER,
            confidence=confidence,
            reasons=reasons,
            raw_scores=raw_scores,
        )

    def _calc_confidence(
        self,
        reasons: list[str],
        raw_scores: dict[str, float],
    ) -> float:
        """计算置信度"""
        base = 0.3
        bonus = len(reasons) * 0.25

        extra = 0.0
        if "total_drop" in raw_scores:
            td = raw_scores["total_drop"]
            if td <= -0.08:
                extra += 0.1

        return min(base + bonus + extra, 1.0)
