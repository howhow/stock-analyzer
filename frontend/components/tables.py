"""
表格组件

数据展示表格
"""

import pandas as pd
import streamlit as st


def render_stock_info_table(info: dict) -> None:
    """
    渲染股票基本信息表格

    Args:
        info: 股票信息字典
    """
    df = pd.DataFrame(
        [
            {"字段": "股票代码", "值": info.get("code", "-")},
            {"字段": "股票名称", "值": info.get("name", "-")},
            {"字段": "所属市场", "值": info.get("market", "-")},
            {"字段": "所属行业", "值": info.get("industry", "-")},
        ]
    )
    st.table(df)


def render_analysis_summary_table(summary: dict) -> None:
    """
    渲染分析摘要表格

    Args:
        summary: 分析摘要字典
    """
    df = pd.DataFrame(
        [
            {"指标": "综合评分", "值": f"{summary.get('total_score', 0):.1f}"},
            {"指标": "基本面评分", "值": f"{summary.get('fundamental_score', 0):.1f}"},
            {"指标": "技术面评分", "值": f"{summary.get('technical_score', 0):.1f}"},
            {"指标": "投资建议", "值": summary.get("recommendation", "-")},
            {"指标": "置信度", "值": f"{summary.get('confidence', 0):.0f}%"},
        ]
    )
    st.table(df)


def render_history_table(histories: list[dict]) -> None:
    """
    渲染分析历史表格

    Args:
        histories: 历史记录列表
    """
    if not histories:
        st.info("暂无分析历史")
        return

    df = pd.DataFrame(
        [
            {
                "日期": h.get("created_at", "-"),
                "股票代码": h.get("stock_code", "-"),
                "股票名称": h.get("stock_name", "-"),
                "评分": f"{h.get('total_score', 0):.1f}",
                "建议": h.get("recommendation", "-"),
                "耗时": f"{h.get('analysis_duration_ms', 0)}ms",
            }
            for h in histories
        ]
    )
    st.dataframe(df, use_container_width=True)


def render_config_table(config: dict) -> None:
    """
    渲染配置信息表格

    Args:
        config: 配置信息字典
    """
    df = pd.DataFrame(
        [
            {"配置项": "OpenAI API Key", "值": config.get("openai_api_key", "-")},
            {"配置项": "OpenAI Base URL", "值": config.get("openai_base_url", "-")},
            {"配置项": "OpenAI Model", "值": config.get("openai_model", "-")},
            {"配置项": "Anthropic API Key", "值": config.get("anthropic_api_key", "-")},
            {"配置项": "Anthropic Model", "值": config.get("anthropic_model", "-")},
            {"配置项": "默认分析类型", "值": config.get("default_analysis_type", "-")},
            {"配置项": "默认分析天数", "值": str(config.get("default_days", 120))},
        ]
    )
    st.table(df)
