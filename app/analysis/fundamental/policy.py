"""
政策影响分析

实现政策对行业和个股的影响评估
"""

from typing import Any

from app.utils.logger import get_logger

logger = get_logger(__name__)


# 政策影响权重（按行业）
POLICY_IMPACT_WEIGHTS: dict[str, float] = {
    "科技": 0.8,  # 高度受政策影响
    "医药": 0.7,
    "能源": 0.7,
    "金融": 0.6,
    "制造": 0.5,
    "消费": 0.3,  # 低度受政策影响
    "default": 0.4,
}


def get_policy_sensitivity(industry_name: str | None) -> str:
    """
    获取政策敏感度

    Args:
        industry_name: 行业名称

    Returns:
        政策敏感度描述
    """
    if not industry_name:
        return "未知"

    # 高敏感行业
    high_sensitivity = ["科技", "医药", "能源", "环保", "教育"]
    for keyword in high_sensitivity:
        if keyword in industry_name:
            return "高敏感"

    # 中敏感行业
    medium_sensitivity = ["金融", "地产", "汽车", "通信"]
    for keyword in medium_sensitivity:
        if keyword in industry_name:
            return "中敏感"

    # 低敏感行业
    return "低敏感"


def analyze_policy_impact(
    industry_name: str | None,
    policy_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    分析政策影响

    Args:
        industry_name: 行业名称
        policy_events: 政策事件列表

    Returns:
        政策影响分析结果
    """
    details = {}
    score: float = 50  # 默认中性分数

    # 政策敏感度
    sensitivity = get_policy_sensitivity(industry_name)
    details["sensitivity"] = sensitivity

    # 如果有具体政策事件
    if policy_events:
        positive_count = sum(1 for e in policy_events if e.get("impact") == "positive")
        negative_count = sum(1 for e in policy_events if e.get("impact") == "negative")

        details["positive_events"] = positive_count  # type: ignore[assignment]
        details["negative_events"] = negative_count  # type: ignore[assignment]

        # 根据正负事件调整分数
        score += positive_count * 10
        score -= negative_count * 10
    else:
        # 无具体事件，根据敏感度给分
        sensitivity_scores = {"高敏感": 50, "中敏感": 60, "低敏感": 70, "未知": 50}
        score = sensitivity_scores.get(sensitivity, 50)

    return {"score": min(max(score, 0), 100), "details": details}


def calculate_policy_score(
    industry_name: str | None,
    policy_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    计算政策评分

    Args:
        industry_name: 行业名称
        policy_events: 政策事件列表

    Returns:
        政策评分结果
    """
    impact_analysis = analyze_policy_impact(industry_name, policy_events)

    # 获取政策影响权重
    from app.analysis.fundamental.industry import get_industry_category

    category = get_industry_category(industry_name)
    weight = POLICY_IMPACT_WEIGHTS.get(category, POLICY_IMPACT_WEIGHTS["default"])

    return {
        "total_score": impact_analysis["score"],
        "sensitivity": impact_analysis["details"]["sensitivity"],
        "impact_weight": weight,
        "details": impact_analysis["details"],
    }
