"""
分析页面 - 股票分析与结果展示
"""

import asyncio
from typing import Any

import pandas as pd
import streamlit as st

from frontend.components.charts import (
    create_candlestick_chart,
    create_indicator_chart,
    create_radar_chart,
    create_score_gauge,
)
from frontend.components.sidebar import render_sidebar
from frontend.components.tables import (
    render_analysis_summary_table,
    render_stock_info_table,
)
from frontend.utils.api_client import get_api_client

# 页面配置
st.set_page_config(
    page_title="股票分析 - Stock Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


async def analyze_stock(
    stock_code: str, analysis_type: str, mode: str = "algorithm"
) -> dict[str, Any]:
    """
    调用分析 API

    Args:
        stock_code: 股票代码
        analysis_type: 分析类型
        mode: 分析模式 (algorithm/ai)

    Returns:
        分析结果
    """
    client = get_api_client()
    return await client.post(
        "/api/v1/analysis/analyze",
        data={
            "stock_code": stock_code,
            "analysis_type": analysis_type,
            "mode": mode,
        },
    )


async def fetch_stock_info(stock_code: str) -> dict[str, Any]:
    """获取股票基本信息"""
    client = get_api_client()
    try:
        return await client.get(f"/api/v1/analysis/info/{stock_code}")
    except Exception:
        return {}


def main() -> None:
    """主函数"""
    # 渲染侧边栏
    render_sidebar()

    # 页面标题
    st.title("📊 股票分析")
    st.markdown("---")

    # 分析参数
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # 检查是否有快速分析的参数
        default_code = st.session_state.pop("quick_analyze_code", "")
        stock_code = st.text_input(
            "股票代码",
            value=default_code,
            placeholder="例如: 600519.SH",
            key="analysis_stock_code",
        )

    with col2:
        default_type = st.session_state.pop("quick_analyze_type", "both")
        analysis_type = st.selectbox(
            "分析类型",
            options=["both", "fundamental", "technical"],
            format_func=lambda x: {
                "both": "综合分析",
                "fundamental": "基本面分析",
                "technical": "技术面分析",
            }[x],
            index=(
                ["both", "fundamental", "technical"].index(default_type)
                if default_type in ["both", "fundamental", "technical"]
                else 0
            ),
            key="analysis_type_select",
        )

    with col3:
        mode = st.selectbox(
            "分析模式",
            options=["algorithm", "ai"],
            format_func=lambda x: {"algorithm": "算法分析", "ai": "AI 分析"}[x],
            key="analysis_mode_select",
        )

    st.markdown("---")

    # 分析按钮
    analyze_button = st.button("🔍 开始分析", type="primary", key="start_analyze")

    # 分析逻辑
    if analyze_button and stock_code:
        with st.spinner(f"正在分析 {stock_code}..."):
            try:
                result = asyncio.run(analyze_stock(stock_code, analysis_type, mode))

                # 保存结果到 session state
                st.session_state.analysis_result = result
                st.session_state.last_analyzed_code = stock_code

                st.success("✅ 分析完成！")

            except Exception as e:
                st.error(f"分析失败: {e}")

    # 显示分析结果
    if "analysis_result" in st.session_state:
        result = st.session_state.analysis_result

        # 股票基本信息
        st.markdown("## 📝 股票信息")
        render_stock_info_table(result.get("stock_info", {}))

        # 评分展示
        st.markdown("---")
        st.markdown("## 📊 分析结果")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            # 综合评分仪表盘
            total_score = result.get("total_score", 0)
            fig_gauge = create_score_gauge(total_score, "综合评分")
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col2:
            # 分项评分雷达图
            scores = {
                "基本面": result.get("fundamental_score", 0),
                "技术面": result.get("technical_score", 0),
                "趋势": result.get("trend_score", 50),
                "成交量": result.get("volume_score", 50),
                "波动性": result.get("volatility_score", 50),
            }
            fig_radar = create_radar_chart(scores, "能力雷达图")
            st.plotly_chart(fig_radar, use_container_width=True)

        with col3:
            # 投资建议
            recommendation = result.get("recommendation", "-")
            confidence = result.get("confidence", 0)

            st.markdown("### 💡 投资建议")
            if recommendation in ["强烈买入", "买入"]:
                st.success(f"**{recommendation}**")
            elif recommendation in ["持有", "观望"]:
                st.info(f"**{recommendation}**")
            else:
                st.warning(f"**{recommendation}**")

            st.markdown(f"**置信度**: {confidence:.0f}%")

        # 详细分析表格
        st.markdown("---")
        st.markdown("## 📋 详细分析")
        render_analysis_summary_table(result)

        # K 线图（如果有数据）
        if "quotes" in result and result["quotes"]:
            st.markdown("---")
            st.markdown("## 📈 K 线图")
            df_quotes = pd.DataFrame(result["quotes"])
            df_quotes["trade_date"] = pd.to_datetime(df_quotes["trade_date"])
            df_quotes.set_index("trade_date", inplace=True)

            fig_kline = create_candlestick_chart(df_quotes, f"{stock_code} K线图")
            st.plotly_chart(fig_kline, use_container_width=True)

            # MACD 指标
            if "macd" in df_quotes.columns:
                st.markdown("### MACD 指标")
                fig_macd = create_indicator_chart(df_quotes, "MACD")
                st.plotly_chart(fig_macd, use_container_width=True)

            # RSI 指标
            if "rsi" in df_quotes.columns:
                st.markdown("### RSI 指标")
                fig_rsi = create_indicator_chart(df_quotes, "RSI")
                st.plotly_chart(fig_rsi, use_container_width=True)

        # AI 分析意见（如果是 AI 模式）
        if mode == "ai" and "ai_analysis" in result:
            st.markdown("---")
            st.markdown("## 🤖 AI 分析意见")
            st.markdown(result["ai_analysis"])

        # 导出报告
        st.markdown("---")
        st.markdown("## 📄 导出报告")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 下载 HTML 报告", key="download_html"):
                st.info("报告生成中...")

        with col2:
            if st.button("📥 下载 Markdown 报告", key="download_md"):
                st.info("报告生成中...")


if __name__ == "__main__":
    main()
