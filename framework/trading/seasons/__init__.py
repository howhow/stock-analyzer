"""四季系统模块

包含:
- SafetyMarginCalculator: 动态安全边际计算
- SeasonsEngine: 四季引擎
- TradingGuard: 四季→五行约束守卫
"""

from framework.trading.seasons.safety_margin import (
    SafetyMarginCalculator,
    SafetyMarginResult,
    MarginLevel,
)
from framework.trading.seasons.engine import (
    Season,
    SeasonState,
    SeasonsEngine,
)
from framework.trading.seasons.guard import (
    GuardAction,
    WuxingAction,
    GuardCheckResult,
    TradingGuard,
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
