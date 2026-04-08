"""
评分系统

实现多维度评分计算
"""

from app.utils.logger import get_logger

logger = get_logger(__name__)


# 长线分析权重（PRD定义）
LONG_TERM_WEIGHTS: dict[str, float] = {
    "company": 0.25,  # 公司质量
    "industry": 0.1875,  # 行业地位
    "market": 0.125,  # 市场环境
    "policy": 0.0625,  # 政策影响
    "trend": 0.375,  # 趋势分析
}

# 短线分析权重
SHORT_TERM_WEIGHTS: dict[str, float] = {
    "momentum": 0.3,  # 动量
    "volume": 0.25,  # 成交量
    "trend": 0.25,  # 趋势
    "volatility": 0.2,  # 波动率
}


class ScoringEngine:
    """
    评分引擎

    负责计算综合评分和信号强度
    """

    @staticmethod
    def calculate_long_term_score(
        company_score: float,
        industry_score: float,
        market_score: float,
        policy_score: float,
        trend_score: float,
    ) -> float:
        """
        计算长线综合评分

        Args:
            company_score: 公司质量评分
            industry_score: 行业地位评分
            market_score: 市场环境评分
            policy_score: 政策影响评分
            trend_score: 趋势分析评分

        Returns:
            综合评分 (0-100)
        """
        weighted_score = (
            company_score * LONG_TERM_WEIGHTS["company"]
            + industry_score * LONG_TERM_WEIGHTS["industry"]
            + market_score * LONG_TERM_WEIGHTS["market"]
            + policy_score * LONG_TERM_WEIGHTS["policy"]
            + trend_score * LONG_TERM_WEIGHTS["trend"]
        )

        return round(weighted_score, 2)

    @staticmethod
    def calculate_short_term_score(
        momentum_score: float,
        volume_score: float,
        trend_score: float,
        volatility_score: float,
    ) -> float:
        """
        计算短线综合评分

        Args:
            momentum_score: 动量评分
            volume_score: 成交量评分
            trend_score: 趋势评分
            volatility_score: 波动率评分

        Returns:
            综合评分 (0-100)
        """
        weighted_score = (
            momentum_score * SHORT_TERM_WEIGHTS["momentum"]
            + volume_score * SHORT_TERM_WEIGHTS["volume"]
            + trend_score * SHORT_TERM_WEIGHTS["trend"]
            + volatility_score * SHORT_TERM_WEIGHTS["volatility"]
        )

        return round(weighted_score, 2)

    @staticmethod
    def calculate_signal_strength(
        trend_score: float,
        volume_score: float,
        momentum_score: float | None = None,
    ) -> float:
        """
        计算信号强度

        Args:
            trend_score: 趋势评分
            volume_score: 成交量评分
            momentum_score: 动量评分（可选）

        Returns:
            信号强度 (0-5)
        """
        # 基础分数
        base_score = (trend_score + volume_score) / 2

        # 如果有动量分数，加入计算
        if momentum_score is not None:
            base_score = base_score * 0.6 + momentum_score * 0.4

        # 映射到0-5
        signal_strength = (base_score / 100) * 5

        return round(signal_strength, 1)

    @staticmethod
    def calculate_opportunity_quality(
        price_position: float,
        trend_direction: int,
        rsi: float | None = None,
    ) -> float:
        """
        计算机会质量

        Args:
            price_position: 价格位置 (0-1)
            trend_direction: 趋势方向 (1: 上涨, -1: 下跌, 0: 震荡)
            rsi: RSI值 (可选)

        Returns:
            机会质量 (0-5)
        """
        score = 0.0

        # 价格位置（低位更好）
        if price_position < 0.3:
            score += 2.0
        elif price_position < 0.5:
            score += 1.5
        elif price_position < 0.7:
            score += 1.0
        else:
            score += 0.5

        # 趋势方向
        if trend_direction > 0:
            score += 2.0
        elif trend_direction == 0:
            score += 1.0
        else:
            score += 0.5

        # RSI指标（超卖更好）
        if rsi is not None:
            if rsi < 30:
                score += 1.0
            elif rsi < 50:
                score += 0.5

        # 归一化到0-5
        return round(min(score, 5.0), 1)

    @staticmethod
    def calculate_risk_level(
        volatility: float,
        debt_ratio: float | None = None,
        price_position: float | None = None,
    ) -> float:
        """
        计算风险等级

        Args:
            volatility: 波动率
            debt_ratio: 资产负债率 (可选)
            price_position: 价格位置 (可选)

        Returns:
            风险等级 (1-5)
        """
        risk = 0.0

        # 波动率风险
        if volatility > 0.5:
            risk += 2.0
        elif volatility > 0.3:
            risk += 1.5
        elif volatility > 0.2:
            risk += 1.0
        else:
            risk += 0.5

        # 资产负债率风险
        if debt_ratio is not None:
            if debt_ratio > 80:
                risk += 2.0
            elif debt_ratio > 60:
                risk += 1.0
            else:
                risk += 0.5

        # 价格位置风险（高位风险更大）
        if price_position is not None:
            if price_position > 0.8:
                risk += 1.5
            elif price_position > 0.6:
                risk += 1.0
            else:
                risk += 0.5

        # 归一化到1-5
        return round(min(max(risk, 1.0), 5.0), 1)

    @staticmethod
    def get_recommendation(total_score: float) -> tuple[str, float]:
        """
        根据综合评分给出投资建议

        Args:
            total_score: 综合评分

        Returns:
            (建议, 置信度)
        """
        if total_score >= 80:
            return "强烈买入", 90
        elif total_score >= 70:
            return "买入", 75
        elif total_score >= 55:
            return "持有", 60
        elif total_score >= 40:
            return "减持", 45
        else:
            return "卖出", 30


def score_to_rating(score: float) -> str:
    """
    将分数转换为评级

    Args:
        score: 分数 (0-100)

    Returns:
        评级 (A/B/C/D/E)
    """
    if score >= 80:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 35:
        return "D"
    else:
        return "E"
