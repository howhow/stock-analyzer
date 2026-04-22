"""四季引擎 — 战略层

四季系统: 基于基本面 + DCF 估值判断当前季节
- 春: DCF低估，建仓
- 夏: 持有中，基本面不变
- 秋: 五行出现"金"形态，减仓评估
- 冬: 估值过高/逻辑变坏，清仓
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from framework.events import Events
from framework.trading.seasons.safety_margin import (
    MarginLevel,
    SafetyMarginCalculator,
    SafetyMarginResult,
)


class Season(str, Enum):
    """四季枚举"""

    SPRING = "spring"  # 春 — 建仓
    SUMMER = "summer"  # 夏 — 持有
    AUTUMN = "autumn"  # 秋 — 减仓评估
    WINTER = "winter"  # 冬 — 清仓


# 安全边际等级 → 季节映射
_LEVEL_TO_SEASON: dict[MarginLevel, Season] = {
    MarginLevel.DEEPLY_UNDERVALUED: Season.SPRING,
    MarginLevel.UNDERVALUED: Season.SPRING,
    MarginLevel.FAIR: Season.SUMMER,
    MarginLevel.OVERVALUED: Season.AUTUMN,
    MarginLevel.DEEPLY_OVERVALUED: Season.WINTER,
}


@dataclass(frozen=True)
class SeasonState:
    """四季状态数据模型"""

    ts_code: str
    season: Season
    confidence: float  # 0.0 ~ 1.0
    safety_margin_result: SafetyMarginResult
    previous_season: Optional[Season] = None

    @property
    def position_guidance(self) -> str:
        """仓位指导"""
        guidance_map: dict[Season, str] = {
            Season.SPRING: "建仓 50-70%",
            Season.SUMMER: "持有，维持仓位",
            Season.AUTUMN: "分批减仓",
            Season.WINTER: "清仓",
        }
        return guidance_map[self.season]


class SeasonsEngine:
    """四季引擎 — 基本面驱动，判断当前季节

    判断逻辑:
    1. DCF 估值 → 安全边际等级
    2. 安全边际等级 → 季节
    3. 季节变化 → 触发 season_changed 事件
    """

    def __init__(
        self,
        safety_margin_calculator: Optional[SafetyMarginCalculator] = None,
    ) -> None:
        self._calculator = safety_margin_calculator or SafetyMarginCalculator()
        self._current_states: dict[str, SeasonState] = {}

    def analyze(
        self,
        ts_code: str,
        dcf_value: float,
        current_price: float,
        beta: Optional[float] = None,
        pe_percentile: Optional[float] = None,
        pb_percentile: Optional[float] = None,
    ) -> SeasonState:
        """分析股票当前季节

        Args:
            ts_code: 股票代码
            dcf_value: DCF 估值
            current_price: 当前价格
            beta: 个股 β 系数
            pe_percentile: PE 历史分位
            pb_percentile: PB 历史分位

        Returns:
            SeasonState
        """
        # 计算安全边际
        margin_result = self._calculator.calculate(
            ts_code=ts_code,
            dcf_value=dcf_value,
            current_price=current_price,
            beta=beta,
            pe_percentile=pe_percentile,
            pb_percentile=pb_percentile,
        )

        # 安全边际等级 → 季节
        season = _LEVEL_TO_SEASON[margin_result.level]

        # 计算置信度
        confidence = self._calc_confidence(margin_result)

        # 获取上一季节
        previous_season: Optional[Season] = None
        if ts_code in self._current_states:
            previous_season = self._current_states[ts_code].season

        # 创建状态
        state = SeasonState(
            ts_code=ts_code,
            season=season,
            confidence=confidence,
            safety_margin_result=margin_result,
            previous_season=previous_season,
        )

        # 季节变化 → 发送事件
        if previous_season is not None and previous_season != season:
            Events.season_changed.send(
                sender=self,
                ts_code=ts_code,
                old_season=previous_season.value,
                new_season=season.value,
                confidence=confidence,
            )

        self._current_states[ts_code] = state
        return state

    def get_current_state(self, ts_code: str) -> Optional[SeasonState]:
        """获取股票当前季节状态"""
        return self._current_states.get(ts_code)

    def _calc_confidence(self, margin_result: SafetyMarginResult) -> float:
        """计算季节判断置信度

        规则:
        - 安全边际绝对值越大 → 置信度越高
        - 有 β 数据时更可靠
        """
        margin_abs = abs(margin_result.safety_margin)

        # 基础置信度: 0.5 ~ 1.0
        base_conf = min(0.5 + margin_abs * 1.5, 1.0)

        # 有 β 数据 → +0.05
        if margin_result.beta is not None:
            base_conf = min(base_conf + 0.05, 1.0)

        # 有 PE/PB 分位 → +0.05
        if margin_result.pe_percentile is not None:
            base_conf = min(base_conf + 0.05, 1.0)

        return round(base_conf, 2)
