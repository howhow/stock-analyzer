"""五行系统模块

包含:
- Detectors: 木/火/金/水识别器
- BayesianTransitionEngine: 贝叶斯转换引擎
- WuxingEngine: 五行状态机
"""

from framework.trading.wuxing.bayesian import (
    LIKELIHOOD_PARAMS,
    PRIORS,
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
from framework.trading.wuxing.engine import WuxingEngine, WuxingState

__all__ = [
    # Detectors
    "WuxingElement",
    "DetectionResult",
    "WoodStateDetector",
    "FireStateDetector",
    "MetalStateDetector",
    "WaterStateDetector",
    # Bayesian
    "BayesianTransitionEngine",
    "BayesianResult",
    "ActionAdvice",
    "PRIORS",
    "LIKELIHOOD_PARAMS",
    # Engine
    "WuxingState",
    "WuxingEngine",
]
