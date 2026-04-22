"""四季→五行约束守卫

核心规则: 五行操作受四季状态约束
- 春: 允许所有五行操作（建仓期）
- 夏: 限制短线仓位比例
- 秋: 禁止新开短线仓位，强制减仓
- 冬: 强制清仓
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Optional

from framework.trading.seasons.engine import Season, SeasonState


class GuardAction(str, Enum):
    """守卫动作"""

    ALLOW = "allow"  # 允许
    BLOCK_NEW = "block_new"  # 禁止新开仓
    REDUCE_SHORT = "reduce_short"  # 减少短线仓位
    FORCE_REDUCE = "force_reduce"  # 强制减仓
    FORCE_LIQUIDATE = "force_liquidate"  # 强制清仓


class WuxingAction(str, Enum):
    """五行操作类型"""

    OPEN_LONG = "open_long"  # 开多
    OPEN_SHORT = "open_short"  # 开空
    ADD_POSITION = "add_position"  # 加仓
    CLOSE_POSITION = "close_position"  # 平仓
    REDUCE_POSITION = "reduce_position"  # 减仓


# 四季 → 五行操作约束映射
SEASON_RULES: dict[Season, dict[WuxingAction, GuardAction]] = {
    Season.SPRING: {
        WuxingAction.OPEN_LONG: GuardAction.ALLOW,
        WuxingAction.OPEN_SHORT: GuardAction.BLOCK_NEW,
        WuxingAction.ADD_POSITION: GuardAction.ALLOW,
        WuxingAction.CLOSE_POSITION: GuardAction.ALLOW,
        WuxingAction.REDUCE_POSITION: GuardAction.ALLOW,
    },
    Season.SUMMER: {
        WuxingAction.OPEN_LONG: GuardAction.ALLOW,
        WuxingAction.OPEN_SHORT: GuardAction.BLOCK_NEW,
        WuxingAction.ADD_POSITION: GuardAction.REDUCE_SHORT,
        WuxingAction.CLOSE_POSITION: GuardAction.ALLOW,
        WuxingAction.REDUCE_POSITION: GuardAction.ALLOW,
    },
    Season.AUTUMN: {
        WuxingAction.OPEN_LONG: GuardAction.BLOCK_NEW,
        WuxingAction.OPEN_SHORT: GuardAction.BLOCK_NEW,
        WuxingAction.ADD_POSITION: GuardAction.BLOCK_NEW,
        WuxingAction.CLOSE_POSITION: GuardAction.ALLOW,
        WuxingAction.REDUCE_POSITION: GuardAction.FORCE_REDUCE,
    },
    Season.WINTER: {
        WuxingAction.OPEN_LONG: GuardAction.BLOCK_NEW,
        WuxingAction.OPEN_SHORT: GuardAction.BLOCK_NEW,
        WuxingAction.ADD_POSITION: GuardAction.BLOCK_NEW,
        WuxingAction.CLOSE_POSITION: GuardAction.FORCE_LIQUIDATE,
        WuxingAction.REDUCE_POSITION: GuardAction.FORCE_LIQUIDATE,
    },
}


@dataclass(frozen=True)
class GuardCheckResult:
    """守卫检查结果"""

    allowed: bool
    action: GuardAction
    season: Season
    wuxing_action: WuxingAction
    reason: str


class TradingGuard:
    """四季→五行约束守卫

    确保:
    - 春季建仓期允许五行操作
    - 夏季限制短线仓位
    - 秋季禁止新开仓，强制减仓
    - 冬季强制清仓
    """

    def check(
        self,
        season_state: SeasonState,
        wuxing_action: WuxingAction,
    ) -> GuardCheckResult:
        """检查五行操作是否被四季状态允许

        Args:
            season_state: 当前四季状态
            wuxing_action: 拟执行的五行操作

        Returns:
            GuardCheckResult
        """
        season = season_state.season
        rules = SEASON_RULES.get(season, {})
        guard_action = rules.get(wuxing_action, GuardAction.BLOCK_NEW)

        allowed = guard_action == GuardAction.ALLOW
        reason = self._build_reason(season, wuxing_action, guard_action)

        return GuardCheckResult(
            allowed=allowed,
            action=guard_action,
            season=season,
            wuxing_action=wuxing_action,
            reason=reason,
        )

    def _build_reason(
        self,
        season: Season,
        wuxing_action: WuxingAction,
        guard_action: GuardAction,
    ) -> str:
        """构建原因说明"""
        season_names: dict[Season, str] = {
            Season.SPRING: "春季(建仓期)",
            Season.SUMMER: "夏季(持有期)",
            Season.AUTUMN: "秋季(减仓期)",
            Season.WINTER: "冬季(清仓期)",
        }

        if guard_action == GuardAction.ALLOW:
            return f"{season_names[season]}: 允许{wuxing_action.value}"

        action_reasons: dict[GuardAction, str] = {
            GuardAction.BLOCK_NEW: "禁止新开仓",
            GuardAction.REDUCE_SHORT: "需减少短线仓位",
            GuardAction.FORCE_REDUCE: "强制减仓",
            GuardAction.FORCE_LIQUIDATE: "强制清仓",
        }

        return f"{season_names[season]}: {action_reasons[guard_action]}"
