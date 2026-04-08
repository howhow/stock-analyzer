"""
交易员角色

负责交易机会识别和风险评估
"""

from typing import Any

import pandas as pd

from app.analysis.base import AnalysisResult, BaseAnalyzer
from app.analysis.indicators import golden_cross, rsi, support_resistance
from app.analysis.scoring import ScoringEngine
from app.models.stock import DailyQuote, FinancialData, StockInfo
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Trader(BaseAnalyzer):
    """
    交易员角色

    职责：
    1. 识别交易机会（短线）
    2. 评估风险水平
    3. 给出买卖建议
    """

    def __init__(self) -> None:
        super().__init__("trader")

    async def analyze(
        self,
        stock_info: StockInfo,
        quotes: list[DailyQuote],
        financial: FinancialData | None = None,
        **kwargs: Any,
    ) -> AnalysisResult:
        """
        执行交易分析

        Args:
            stock_info: 股票基本信息
            quotes: 日线行情数据
            financial: 财务数据
            **kwargs: 其他参数

        Returns:
            分析结果
        """
        result = AnalysisResult(self.name)

        # 数据验证
        if not self.validate_data(quotes, min_days=20):
            result.add_warning("数据不足，至少需要20天数据")
            return result

        # 提取价格序列
        prices = self.extract_price_series(quotes)
        close_series = pd.Series(prices["close"])
        high_series = pd.Series(prices["high"])
        low_series = pd.Series(prices["low"])

        # 1. 计算信号强度
        signal_strength = self._calculate_signal_strength(
            close_series, high_series, low_series, result
        )
        result.add_score("signal_strength", signal_strength)

        # 2. 计算机会质量
        opportunity_quality = self._calculate_opportunity_quality(
            close_series, high_series, low_series, result
        )
        result.add_score("opportunity_quality", opportunity_quality)

        # 3. 计算风险等级
        risk_level = self._calculate_risk_level(
            close_series, high_series, low_series, financial, result
        )
        result.add_score("risk_level", risk_level)

        # 4. 计算综合评分
        total_score = self._calculate_total_score(
            signal_strength, opportunity_quality, risk_level
        )
        result.add_score("total", total_score)

        # 5. 生成交易建议
        recommendation, confidence = ScoringEngine.get_recommendation(total_score)
        result.add_detail("recommendation", recommendation)
        result.add_detail("confidence", confidence)
        result.add_signal(f"建议: {recommendation} (置信度: {confidence}%)")

        return result

    def _calculate_signal_strength(
        self,
        close: pd.Series,
        high: pd.Series,
        low: pd.Series,
        result: AnalysisResult,
    ) -> float:
        """计算信号强度"""
        # 趋势信号
        golden = golden_cross(close, 5, 20).iloc[-1]
        trend_score = 50 + golden * 20

        # RSI信号
        rsi_value = rsi(close, 14).iloc[-1]
        if rsi_value < 30:
            rsi_score = 80
        elif rsi_value > 70:
            rsi_score = 30
        else:
            rsi_score = 50

        # 综合信号强度
        signal = ScoringEngine.calculate_signal_strength(
            trend_score, rsi_score, rsi_score
        )

        result.add_detail(
            "signal_details",
            {
                "trend_score": float(trend_score),
                "rsi_score": float(rsi_score),
                "golden_cross": int(golden),
                "rsi": float(rsi_value),
            },
        )

        return signal

    def _calculate_opportunity_quality(
        self,
        close: pd.Series,
        high: pd.Series,
        low: pd.Series,
        result: AnalysisResult,
    ) -> float:
        """计算机会质量"""
        # 支撑阻力位
        sr = support_resistance(high, low, close, period=20)
        price_position = sr["current_position"]

        # 趋势方向
        price_change = (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20]
        trend_direction = (
            1 if price_change > 0.05 else (-1 if price_change < -0.05 else 0)
        )

        # RSI
        rsi_value = rsi(close, 14).iloc[-1]

        # 计算机会质量
        quality = ScoringEngine.calculate_opportunity_quality(
            price_position, trend_direction, float(rsi_value)
        )

        result.add_detail(
            "opportunity_details",
            {
                "price_position": float(price_position),
                "support": float(sr["support"]),
                "resistance": float(sr["resistance"]),
                "trend_direction": int(trend_direction),
            },
        )

        return quality

    def _calculate_risk_level(
        self,
        close: pd.Series,
        high: pd.Series,
        low: pd.Series,
        financial: FinancialData | None,
        result: AnalysisResult,
    ) -> float:
        """计算风险等级"""
        # 波动率
        returns = close.pct_change()
        volatility = returns.std() * (252**0.5)  # 年化波动率

        # 价格位置
        high_20 = high.rolling(window=20).max().iloc[-1]
        low_20 = low.rolling(window=20).min().iloc[-1]
        price_position = (close.iloc[-1] - low_20) / (high_20 - low_20)

        # 资产负债率
        debt_ratio = financial.debt_ratio if financial else None

        # 计算风险等级
        risk = ScoringEngine.calculate_risk_level(
            float(volatility),
            debt_ratio,
            float(price_position),
        )

        result.add_detail(
            "risk_details",
            {
                "volatility": float(volatility),
                "price_position": float(price_position),
                "debt_ratio": debt_ratio,
            },
        )

        return risk

    def _calculate_total_score(
        self,
        signal_strength: float,
        opportunity_quality: float,
        risk_level: float,
    ) -> float:
        """计算综合评分"""
        # 信号强度 (0-5) → 0-100
        signal_score = signal_strength * 20

        # 机会质量 (0-5) → 0-100
        opportunity_score = opportunity_quality * 20

        # 风险等级 (1-5) → 100-0 (风险越高分数越低)
        risk_score = (6 - risk_level) * 20

        # 加权平均
        total = signal_score * 0.3 + opportunity_score * 0.4 + risk_score * 0.3

        return round(total, 2)
