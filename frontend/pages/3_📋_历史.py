"""
历史页面 - 分析历史记录
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import streamlit as st

from frontend.components.sidebar import render_sidebar
from frontend.components.tables import render_history_table
from frontend.utils.api_client import get_api_client

# 页面配置
st.set_page_config(
    page_title="分析历史 - Stock Analyzer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)


async def get_analysis_histories(
    user_id: str,
    stock_code: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    获取分析历史

    Args:
        user_id: 用户 ID
        stock_code: 股票代码（可选筛选）
        limit: 返回数量限制

    Returns:
        历史记录列表
    """
    client = get_api_client()
    params = {"limit": limit}
    if stock_code:
        params["stock_code"] = stock_code

    try:
        return await client.get(f"/api/v1/analysis/history/{user_id}", params=params)
    except Exception:
        return []


async def get_analysis_detail(history_id: int) -> dict[str, Any]:
    """获取分析详情"""
    client = get_api_client()
    try:
        return await client.get(f"/api/v1/analysis/detail/{history_id}")
    except Exception:
        return {}


def main() -> None:
    """主函数"""
    # 渲染侧边栏
    sidebar_config = render_sidebar()
    user_id = sidebar_config["user_id"]

    # 页面标题
    st.title("📋 分析历史")
    st.markdown("查看和管理您的分析历史记录")
    st.markdown("---")

    # 筛选条件
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        filter_stock_code = st.text_input(
            "按股票代码筛选",
            placeholder="例如: 600519.SH",
            key="filter_stock_code",
        )

    with col2:
        filter_days = st.selectbox(
            "时间范围",
            options=[7, 30, 90, 180, 365],
            format_func=lambda x: f"最近 {x} 天",
            index=1,
            key="filter_days",
        )

    with col3:
        filter_limit = st.selectbox(
            "显示数量",
            options=[10, 20, 50, 100],
            index=1,
            key="filter_limit",
        )

    # 查询按钮
    if st.button("🔍 查询", type="primary", key="search_history"):
        st.session_state.history_search = True

    st.markdown("---")

    # 获取历史记录
    if "history_search" not in st.session_state:
        st.session_state.history_search = True

    if st.session_state.history_search:
        with st.spinner("加载历史记录..."):
            try:
                histories = asyncio.run(
                    get_analysis_histories(
                        user_id,
                        stock_code=filter_stock_code if filter_stock_code else None,
                        limit=filter_limit,
                    )
                )

                # 按时间范围筛选
                if histories:
                    cutoff_date = datetime.now() - timedelta(days=filter_days)
                    histories = [
                        h
                        for h in histories
                        if datetime.fromisoformat(h.get("created_at", "2000-01-01"))
                        >= cutoff_date
                    ]

                st.session_state.histories = histories

            except Exception as e:
                st.error(f"获取历史记录失败: {e}")
                st.session_state.histories = []

    # 显示历史记录
    if "histories" in st.session_state:
        histories = st.session_state.histories

        if histories:
            st.markdown(f"### 共找到 {len(histories)} 条记录")
            render_history_table(histories)

            # 详细查看
            st.markdown("---")
            st.markdown("### 📊 详细查看")

            selected_id = st.selectbox(
                "选择要查看的记录",
                options=[h.get("id") for h in histories],
                format_func=lambda x: next(
                    (
                        f"{h.get('stock_code')} - {h.get('created_at')}"
                        for h in histories
                        if h.get("id") == x
                    ),
                    str(x),
                ),
                key="select_history_id",
            )

            if selected_id and st.button("查看详情", key="view_detail"):
                with st.spinner("加载详情..."):
                    try:
                        detail = asyncio.run(get_analysis_detail(selected_id))

                        if detail:
                            # 显示详情
                            st.markdown("#### 分析结果")
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric(
                                    "综合评分", f"{detail.get('total_score', 0):.1f}"
                                )

                            with col2:
                                st.metric(
                                    "基本面评分",
                                    f"{detail.get('fundamental_score', 0):.1f}",
                                )

                            with col3:
                                st.metric(
                                    "技术面评分",
                                    f"{detail.get('technical_score', 0):.1f}",
                                )

                            # 投资建议
                            st.markdown(
                                f"**投资建议**: {detail.get('recommendation', '-')}"
                            )

                            # 详细分析结果
                            if "analysis_result" in detail:
                                st.markdown("---")
                                st.markdown("#### 完整分析结果")
                                st.json(detail["analysis_result"])

                        else:
                            st.warning("未找到详细信息")

                    except Exception as e:
                        st.error(f"获取详情失败: {e}")

        else:
            st.info("暂无分析历史记录")

            st.markdown(
                """
            ### 🚀 开始分析

            您还没有任何分析记录，前往 [分析页面](/分析) 开始您的第一次分析吧！
            """
            )

    # 导出功能
    st.markdown("---")
    st.markdown("### 📥 导出数据")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("导出 CSV", key="export_csv"):
            if "histories" in st.session_state and st.session_state.histories:
                st.info("CSV 导出功能开发中...")
            else:
                st.warning("暂无数据可导出")

    with col2:
        if st.button("导出 JSON", key="export_json"):
            if "histories" in st.session_state and st.session_state.histories:
                st.info("JSON 导出功能开发中...")
            else:
                st.warning("暂无数据可导出")


if __name__ == "__main__":
    main()
