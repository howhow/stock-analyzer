"""四季系统模块

包含:
- SafetyMarginCalculator: 动态安全边际计算
- SeasonsEngine: 四季引擎
- TradingGuard: 四季→五行约束守卫
"""

from framework.trading.seasons.engine import Season, SeasonsEngine, SeasonState
from framework.trading.seasons.guard import (
    GuardAction,
    GuardCheckResult,
    TradingGuard,
    WuxingAction,
)
from framework.trading.seasons.safety_margin import (
    MarginLevel,
    SafetyMarginCalculator,
    SafetyMarginResult,
)

__all__ = [
    # Safety Margin
    "SafetyMarginCalculator",
    "SafetyMarginResult",
    "MarginLevel",
    # Seasons Engine
    "Season",
    "SeasonState",
    "SeasonsEngine",
    # Trading Guard
    "GuardAction",
    "WuxingAction",
    "GuardCheckResult",
    "TradingGuard",
]
