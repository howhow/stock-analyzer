"""
分析师角色

负责基本面和技术面分析
"""

from typing import Any

import pandas as pd

from app.analysis.base import AnalysisResult, BaseAnalyzer
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
    trend_direction,
)
from app.models.stock import DailyQuote, FinancialData, StockInfo
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Analyst(BaseAnalyzer):
    """
    分析师角色

    职责：
    1. 基本面分析：财务、行业、政策
    2. 技术面分析：趋势、动量、波动率
    3. 生成分析报告和评分
    """

    def __init__(self) -> None:
        super().__init__("analyst")

    async def analyze(
        self,
        stock_info: StockInfo,
        quotes: list[DailyQuote],
        financial: FinancialData | None = None,
        **kwargs: Any,
    ) -> AnalysisResult:
        """
        执行完整分析

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

        # 1. 基本面分析
        fundamental_score = await self._analyze_fundamental(
            stock_info, financial, result
        )
        result.add_score("fundamental", fundamental_score)

        # 2. 技术面分析
        technical_score = await self._analyze_technical(prices, result)
        result.add_score("technical", technical_score)

        # 3. 综合评分
        total_score = fundamental_score * 0.4 + technical_score * 0.6
        result.add_score("total", total_score)

        return result

    async def _analyze_fundamental(
        self,
        stock_info: StockInfo,
        financial: FinancialData | None,
        result: AnalysisResult,
    ) -> float:
        """基本面分析"""
        scores = []

        # 财务分析
        financial_result = calculate_financial_score(financial)
        financial_score = financial_result.get("total_score", 50)
        scores.append(financial_score)
        result.add_detail("financial", financial_result)

        # 行业分析
        industry_result = calculate_industry_score(stock_info.industry)
        industry_score = industry_result.get("total_score", 50)
        scores.append(industry_score)
        result.add_detail("industry", industry_result)

        # 政策分析
        policy_result = calculate_policy_score(stock_info.industry)
        policy_score = policy_result.get("total_score", 50)
        scores.append(policy_score)
        result.add_detail("policy", policy_result)

        # 基本面综合评分
        return sum(scores) / len(scores) if scores else 50

    async def _analyze_technical(
        self,
        prices: dict[str, list[float]],
        result: AnalysisResult,
    ) -> float:
        """技术面分析"""
        close = prices["close"]
        high = prices["high"]
        low = prices["low"]
        volume = prices["volume"]

        scores = []

        # 1. 趋势分析
        trend_score = self._analyze_trend(close, result)
        scores.append(trend_score)

        # 2. 动量分析
        momentum_score = self._analyze_momentum(close, result)
        scores.append(momentum_score)

        # 3. 波动率分析
        volatility_score = self._analyze_volatility(high, low, close, result)
        scores.append(volatility_score)

        # 4. 成交量分析
        volume_score = self._analyze_volume(close, volume, result)
        scores.append(volume_score)

        # 技术面综合评分
        return sum(scores) / len(scores)

    def _analyze_trend(
        self,
        close: list[float],
        result: AnalysisResult,
    ) -> float:
        """趋势分析"""
        close_series = pd.Series(close)

        # EMA趋势
        ema5 = ema(close_series, 5)
        ema20 = ema(close_series, 20)
        trend = trend_direction(close_series, 5, 20).iloc[-1]

        # 金叉死叉信号
        golden = golden_cross(close_series, 5, 20).iloc[-1]

        # MACD
        macd_result = macd(close_series)
        macd_hist = macd_result["histogram"].iloc[-1]

        # 评分计算
        score = 50

        # 趋势方向
        if trend > 0:
            score += 20
            result.add_signal("上涨趋势")
        elif trend < 0:
            score -= 20
            result.add_signal("下跌趋势")
        else:
            result.add_signal("震荡整理")

        # 金叉死叉
        if golden > 0:
            score += 15
            result.add_signal("金叉买入信号")
        elif golden < 0:
            score -= 10
            result.add_signal("死叉卖出信号")

        # MACD柱状图
        if macd_hist > 0:
            score += 10
        else:
            score -= 5

        result.add_detail(
            "trend",
            {
                "direction": int(trend),
                "golden_cross": int(golden),
                "macd_histogram": float(macd_hist),
            },
        )

        return min(max(score, 0), 100)

    def _analyze_momentum(
        self,
        close: list[float],
        result: AnalysisResult,
    ) -> float:
        """动量分析"""
        close_series = pd.Series(close)

        # RSI
        rsi_series = rsi(close_series, 14)
        rsi_value = rsi_series.iloc[-1]

        # 评分计算
        score = 50

        if rsi_value > 70:
            score -= 20
            result.add_signal("RSI超买")
        elif rsi_value < 30:
            score += 20
            result.add_signal("RSI超卖")
        elif 40 <= rsi_value <= 60:
            score += 10
            result.add_signal("RSI中性")

        result.add_detail("momentum", {"rsi": float(rsi_value)})

        return min(max(score, 0), 100)

    def _analyze_volatility(
        self,
        high: list[float],
        low: list[float],
        close: list[float],
        result: AnalysisResult,
    ) -> float:
        """波动率分析"""
        high_series = pd.Series(high)
        low_series = pd.Series(low)
        close_series = pd.Series(close)

        # ATR
        atr_series = atr(high_series, low_series, close_series, 14)
        atr_value = atr_series.iloc[-1]

        # ATR百分比
        atr_pct = (atr_value / close_series.iloc[-1]) * 100

        # 评分计算（波动率适中为佳）
        score = 50

        if atr_pct < 1:
            score += 20
            result.add_signal("低波动率")
        elif atr_pct < 3:
            score += 10
            result.add_signal("正常波动率")
        elif atr_pct > 5:
            score -= 20
            result.add_signal("高波动率风险")

        result.add_detail("volatility", {"atr_pct": float(atr_pct)})

        return min(max(score, 0), 100)

    def _analyze_volume(
        self,
        close: list[float],
        volume: list[float],
        result: AnalysisResult,
    ) -> float:
        """成交量分析"""
        close_series = pd.Series(close)
        volume_series = pd.Series(volume)

        # 量比
        vol_ma = volume_series.rolling(window=20).mean()
        vol_ratio = volume_series.iloc[-1] / vol_ma.iloc[-1]

        # 价格变化
        price_change = (
            close_series.iloc[-1] - close_series.iloc[-2]
        ) / close_series.iloc[-2]

        # 评分计算
        score = 50

        # 放量上涨
        if vol_ratio > 1.5 and price_change > 0:
            score += 30
            result.add_signal("放量上涨")
        # 放量下跌
        elif vol_ratio > 1.5 and price_change < 0:
            score -= 20
            result.add_signal("放量下跌")
        # 缩量
        elif vol_ratio < 0.5:
            score += 10
            result.add_signal("缩量调整")

        result.add_detail("volume", {"volume_ratio": float(vol_ratio)})

        return min(max(score, 0), 100)
