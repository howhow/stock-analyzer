"""五行系统模块

包含:
- Detectors: 木/火/金/水识别器
- BayesianTransitionEngine: 贝叶斯转换引擎
- WuxingEngine: 五行状态机
"""

from framework.trading.wuxing.detectors import (
    WuxingElement,
    DetectionResult,
    WoodStateDetector,
    FireStateDetector,
    MetalStateDetector,
    WaterStateDetector,
)
from framework.trading.wuxing.bayesian import (
    BayesianTransitionEngine,
    BayesianResult,
    ActionAdvice,
    PRIORS,
    LIKELIHOOD_PARAMS,
)
from framework.trading.wuxing.engine import (
    WuxingState,
    WuxingEngine,
)

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
