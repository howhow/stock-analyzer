"""
财务指标分析

实现财务数据分析和评分
"""

from typing import Any

from app.models.stock import FinancialData
from app.utils.logger import get_logger

logger = get_logger(__name__)


def analyze_profitability(financial: FinancialData | None) -> dict[str, Any]:
    """
    分析盈利能力

    Args:
        financial: 财务数据

    Returns:
        盈利能力分析结果
    """
    if not financial:
        return {"score": 0, "details": "无财务数据"}

    details = {}
    score = 0

    # ROE分析
    if financial.roe is not None:
        if financial.roe > 20:
            details["roe"] = "优秀"
            score += 30
        elif financial.roe > 15:
            details["roe"] = "良好"
            score += 20
        elif financial.roe > 10:
            details["roe"] = "一般"
            score += 10
        else:
            details["roe"] = "较差"
            score += 5
    else:
        details["roe"] = "无数据"

    # 净利润分析
    if financial.net_profit is not None:
        if financial.net_profit > 0:
            details["net_profit"] = "盈利"
            score += 20
        else:
            details["net_profit"] = "亏损"
    else:
        details["net_profit"] = "无数据"

    # 市盈率分析
    if financial.pe_ratio is not None:
        if financial.pe_ratio < 15:
            details["pe_ratio"] = "低估"
            score += 20
        elif financial.pe_ratio < 30:
            details["pe_ratio"] = "合理"
            score += 15
        elif financial.pe_ratio < 50:
            details["pe_ratio"] = "偏高"
            score += 5
        else:
            details["pe_ratio"] = "高估"
    else:
        details["pe_ratio"] = "无数据"

    # 市净率分析
    if financial.pb_ratio is not None:
        if financial.pb_ratio < 2:
            details["pb_ratio"] = "低估"
            score += 15
        elif financial.pb_ratio < 4:
            details["pb_ratio"] = "合理"
            score += 10
        else:
            details["pb_ratio"] = "偏高"
            score += 5
    else:
        details["pb_ratio"] = "无数据"

    return {"score": min(score, 100), "details": details}


def analyze_solvency(financial: FinancialData | None) -> dict[str, Any]:
    """
    分析偿债能力

    Args:
        financial: 财务数据

    Returns:
        偿债能力分析结果
    """
    if not financial:
        return {"score": 0, "details": "无财务数据"}

    details = {}
    score = 0

    # 资产负债率分析
    if financial.debt_ratio is not None:
        if financial.debt_ratio < 40:
            details["debt_ratio"] = "低风险"
            score += 40
        elif financial.debt_ratio < 60:
            details["debt_ratio"] = "适中"
            score += 30
        elif financial.debt_ratio < 80:
            details["debt_ratio"] = "较高风险"
            score += 15
        else:
            details["debt_ratio"] = "高风险"
            score += 5
    else:
        details["debt_ratio"] = "无数据"
        score += 20  # 无数据给中等分

    # 总资产和总负债分析
    if financial.total_assets is not None and financial.total_liabilities is not None:
        if financial.total_assets > financial.total_liabilities:
            details["asset_status"] = "资产>负债"
            score += 30
        else:
            details["asset_status"] = "资不抵债"
            score += 5
    else:
        details["asset_status"] = "无数据"

    return {"score": min(score, 100), "details": details}


def analyze_growth(financial: FinancialData | None) -> dict[str, Any]:
    """
    分析成长能力

    Args:
        financial: 财务数据

    Returns:
        成长能力分析结果
    """
    if not financial:
        return {"score": 0, "details": "无财务数据"}

    details = {}
    score = 50  # 默认中等分数

    # 营收分析
    if financial.revenue is not None:
        if financial.revenue > 1_000_000_000:  # 10亿
            details["revenue_scale"] = "大型企业"
            score += 20
        elif financial.revenue > 100_000_000:  # 1亿
            details["revenue_scale"] = "中型企业"
            score += 15
        else:
            details["revenue_scale"] = "小型企业"
            score += 10
    else:
        details["revenue_scale"] = "无数据"

    # ROE作为成长性指标
    if financial.roe is not None:
        if financial.roe > 20:
            details["growth_potential"] = "高成长"
            score += 20
        elif financial.roe > 15:
            details["growth_potential"] = "稳健成长"
            score += 15
        else:
            details["growth_potential"] = "低成长"
            score += 10
    else:
        details["growth_potential"] = "无数据"

    return {"score": min(score, 100), "details": details}


def calculate_financial_score(financial: FinancialData | None) -> dict[str, Any]:
    """
    计算综合财务评分

    Args:
        financial: 财务数据

    Returns:
        综合评分结果
    """
    if not financial:
        return {
            "total_score": 0,
            "profitability": {"score": 0, "details": "无数据"},
            "solvency": {"score": 0, "details": "无数据"},
            "growth": {"score": 0, "details": "无数据"},
        }

    profitability = analyze_profitability(financial)
    solvency = analyze_solvency(financial)
    growth = analyze_growth(financial)

    # 综合评分 (加权平均)
    total_score = (
        profitability["score"] * 0.4 + solvency["score"] * 0.3 + growth["score"] * 0.3
    )

    return {
        "total_score": round(total_score, 2),
        "profitability": profitability,
        "solvency": solvency,
        "growth": growth,
    }
