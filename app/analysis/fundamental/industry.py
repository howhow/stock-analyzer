"""
行业分析

实现行业比较和评分
"""

from typing import Any

from app.utils.logger import get_logger

logger = get_logger(__name__)


# 行业分类和权重
INDUSTRY_WEIGHTS: dict[str, dict[str, float]] = {
    "科技": {"growth": 0.4, "profitability": 0.3, "valuation": 0.3},
    "消费": {"growth": 0.3, "profitability": 0.4, "valuation": 0.3},
    "金融": {"growth": 0.2, "profitability": 0.4, "valuation": 0.4},
    "医药": {"growth": 0.4, "profitability": 0.3, "valuation": 0.3},
    "制造": {"growth": 0.3, "profitability": 0.4, "valuation": 0.3},
    "能源": {"growth": 0.2, "profitability": 0.3, "valuation": 0.5},
    "default": {"growth": 0.3, "profitability": 0.4, "valuation": 0.3},
}


def get_industry_category(industry_name: str | None) -> str:
    """
    获取行业大类

    Args:
        industry_name: 行业名称

    Returns:
        行业大类
    """
    if not industry_name:
        return "default"

    # 行业映射
    industry_map = {
        "科技": ["软件", "电子", "通信", "计算机", "半导体", "芯片"],
        "消费": ["食品", "饮料", "家电", "零售", "服装", "白酒"],
        "金融": ["银行", "保险", "证券", "信托"],
        "医药": ["医药", "生物", "医疗", "制药"],
        "制造": ["机械", "汽车", "化工", "建材", "钢铁"],
        "能源": ["石油", "煤炭", "电力", "新能源", "光伏"],
    }

    for category, keywords in industry_map.items():
        for keyword in keywords:
            if keyword in industry_name:
                return category

    return "default"


def analyze_industry_position(
    industry_name: str | None,
    industry_rank: int | None = None,
) -> dict[str, Any]:
    """
    分析行业地位

    Args:
        industry_name: 行业名称
        industry_rank: 行业排名（1-100）

    Returns:
        行业地位分析结果
    """
    details = {}
    score: float = 50  # 默认中等分数

    # 行业分类
    category = get_industry_category(industry_name)
    details["category"] = category

    # 行业排名分析
    if industry_rank is not None:
        if industry_rank <= 10:
            details["position"] = "龙头"
            score += 40
        elif industry_rank <= 30:
            details["position"] = "领先"
            score += 25
        elif industry_rank <= 50:
            details["position"] = "中游"
            score += 15
        else:
            details["position"] = "落后"
            score += 5
    else:
        details["position"] = "未知"

    # 行业景气度（简化版，实际应从外部数据获取）
    industry_prospects = {
        "科技": 85,
        "消费": 75,
        "金融": 70,
        "医药": 80,
        "制造": 65,
        "能源": 70,
        "default": 60,
    }
    details["prospect_score"] = industry_prospects.get(category, 60)

    return {"score": min(score, 100), "details": details}


def calculate_industry_score(
    industry_name: str | None,
    industry_rank: int | None = None,
) -> dict[str, Any]:
    """
    计算行业评分

    Args:
        industry_name: 行业名称
        industry_rank: 行业排名

    Returns:
        行业评分结果
    """
    position_analysis = analyze_industry_position(industry_name, industry_rank)

    # 获取行业权重
    category = get_industry_category(industry_name)
    weights = INDUSTRY_WEIGHTS.get(category, INDUSTRY_WEIGHTS["default"])

    return {
        "total_score": position_analysis["score"],
        "position": position_analysis["details"]["position"],
        "category": category,
        "weights": weights,
        "details": position_analysis["details"],
    }
