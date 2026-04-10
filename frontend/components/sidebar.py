"""
侧边栏组件

全局导航和配置
"""

from typing import Any

import streamlit as st


def render_sidebar() -> dict[str, Any]:
    """
    渲染侧边栏

    Returns:
        用户配置信息
    """
    with st.sidebar:
        st.title("📊 Stock Analyzer")
        st.markdown("---")

        # 用户信息
        if "user_id" not in st.session_state:
            st.session_state.user_id = "default_user"

        user_id = st.text_input(
            "用户 ID",
            value=st.session_state.user_id,
            key="user_id_input",
        )
        st.session_state.user_id = user_id

        st.markdown("---")

        # 快速链接
        st.markdown("### 📌 快速链接")
        st.markdown("- [📊 股票分析](/分析)")
        st.markdown("- [⚙️ AI 配置](/配置)")
        st.markdown("- [📋 分析历史](/历史)")

        st.markdown("---")

        # 系统状态
        st.markdown("### 🔧 系统状态")
        if "system_status" in st.session_state:
            status = st.session_state.system_status
            if status == "healthy":
                st.success("✅ 系统正常")
            else:
                st.warning("⚠️ 系统异常")
        else:
            st.info("🔄 系统状态未知")

        st.markdown("---")

        # 版本信息
        st.markdown("### 📝 版本信息")
        st.markdown("- Version: 1.1.0")
        st.markdown("- Backend: FastAPI")
        st.markdown("- Frontend: Streamlit")

        return {
            "user_id": user_id,
        }
