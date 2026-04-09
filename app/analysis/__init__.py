"""
分析引擎模块

提供股票分析的核心功能
"""

from app.analysis.analyst import Analyst
from app.analysis.base import AnalyzerResult, BaseAnalyzer
from app.analysis.fundamental import (
    calculate_financial_score,
    calculate_industry_score,
    calculate_policy_score,
)
from app.analysis.indicators import (
    atr,
    bollinger_bands,
    ema,
    golden_cross,
    macd,
    rsi,
    sma,
    support_resistance,
)
from app.analysis.scoring import ScoringEngine, score_to_rating
from app.analysis.system import SystemAnalyzer
from app.analysis.trader import Trader

__all__ = [
    # 分析器
    "BaseAnalyzer",
    "AnalyzerResult",
    "Analyst",
    "Trader",
    "SystemAnalyzer",
    # 评分系统
    "ScoringEngine",
    "score_to_rating",
    # 基本面分析
    "calculate_financial_score",
    "calculate_industry_score",
    "calculate_policy_score",
    # 技术指标（常用）
    "sma",
    "ema",
    "macd",
    "rsi",
    "atr",
    "bollinger_bands",
    "golden_cross",
    "support_resistance",
]
