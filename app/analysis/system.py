"""
系统角色

负责系统级分析和自动化决策
"""

from typing import Any

from app.analysis.analyst import Analyst
from app.analysis.base import AnalysisResult, BaseAnalyzer
from app.analysis.scoring import ScoringEngine
from app.analysis.trader import Trader
from app.models.stock import DailyQuote, FinancialData, StockInfo
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SystemAnalyzer(BaseAnalyzer):
    """
    系统分析角色

    职责：
    1. 协调Analyst和Trader的分析结果
    2. 生成最终的投资建议
    3. 计算置信度
    """

    def __init__(self) -> None:
        super().__init__("system")
        self.analyst = Analyst()
        self.trader = Trader()

    async def analyze(
        self,
        stock_info: StockInfo,
        quotes: list[DailyQuote],
        financial: FinancialData | None = None,
        analysis_type: str = "long",
        **kwargs: Any,
    ) -> AnalysisResult:
        """
        执行系统级分析

        Args:
            stock_info: 股票基本信息
            quotes: 日线行情数据
            financial: 财务数据
            analysis_type: 分析类型 (long/short)
            **kwargs: 其他参数

        Returns:
            分析结果
        """
        result = AnalysisResult(self.name)

        # 数据验证
        if not self.validate_data(quotes, min_days=20):
            result.add_warning("数据不足，至少需要20天数据")
            return result

        # 执行分析师和交易员分析
        analyst_result = await self.analyst.analyze(stock_info, quotes, financial)
        trader_result = await self.trader.analyze(stock_info, quotes, financial)

        # 合并结果
        result.add_detail("analyst", analyst_result.to_dict())
        result.add_detail("trader", trader_result.to_dict())

        # 计算综合评分
        if analysis_type == "long":
            total_score = self._calculate_long_term_score(analyst_result, trader_result)
        else:
            total_score = self._calculate_short_term_score(
                analyst_result, trader_result
            )

        result.add_score("total", total_score)

        # 生成建议
        recommendation, confidence = ScoringEngine.get_recommendation(total_score)
        result.add_detail("recommendation", recommendation)
        result.add_detail("confidence", confidence)
        result.add_detail("analysis_type", analysis_type)

        # 合并信号
        for signal in analyst_result.signals:
            result.add_signal(f"[分析师] {signal}")
        for signal in trader_result.signals:
            result.add_signal(f"[交易员] {signal}")

        result.add_signal(f"[系统] 综合建议: {recommendation} (置信度: {confidence}%)")

        # 合并警告
        for warning in analyst_result.warnings:
            result.add_warning(warning)
        for warning in trader_result.warnings:
            result.add_warning(warning)

        return result

    def _calculate_long_term_score(
        self,
        analyst_result: AnalysisResult,
        trader_result: AnalysisResult,
    ) -> float:
        """计算长线评分"""
        # 获取各维度分数
        fundamental_score = analyst_result.scores.get("fundamental", 50)
        technical_score = analyst_result.scores.get("technical", 50)
        signal_strength = trader_result.scores.get("signal_strength", 2.5)
        opportunity_quality = trader_result.scores.get("opportunity_quality", 2.5)
        risk_level = trader_result.scores.get("risk_level", 3)

        # 信号强度和质量转换为100分制
        signal_score = signal_strength * 20
        opportunity_score = opportunity_quality * 20

        # 风险转换（风险越低分数越高）
        risk_score = (6 - risk_level) * 20

        # 长线权重
        total = (
            fundamental_score * 0.25
            + technical_score * 0.25
            + signal_score * 0.2
            + opportunity_score * 0.15
            + risk_score * 0.15
        )

        return round(total, 2)

    def _calculate_short_term_score(
        self,
        analyst_result: AnalysisResult,
        trader_result: AnalysisResult,
    ) -> float:
        """计算短线评分"""
        # 短线更看重交易员的分析
        technical_score = analyst_result.scores.get("technical", 50)
        signal_strength = trader_result.scores.get("signal_strength", 2.5)
        opportunity_quality = trader_result.scores.get("opportunity_quality", 2.5)
        risk_level = trader_result.scores.get("risk_level", 3)

        # 转换为100分制
        signal_score = signal_strength * 20
        opportunity_score = opportunity_quality * 20
        risk_score = (6 - risk_level) * 20

        # 短线权重
        total = (
            technical_score * 0.2
            + signal_score * 0.3
            + opportunity_score * 0.3
            + risk_score * 0.2
        )

        return round(total, 2)
