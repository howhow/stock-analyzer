"""
Stock Analyzer - Streamlit 主入口

主页：系统概览、快速分析入口
"""

import asyncio
from typing import Any

import streamlit as st

from frontend.components.charts import create_score_gauge
from frontend.components.sidebar import render_sidebar
from frontend.components.tables import render_stock_info_table
from frontend.utils.api_client import get_api_client

# 页面配置
st.set_page_config(
    page_title="Stock Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


async def fetch_health_status() -> dict[str, Any]:
    """获取系统健康状态"""
    client = get_api_client()
    try:
        return await client.get("/api/v1/health")
    except Exception:
        return {"status": "unhealthy"}


async def fetch_user_config(user_id: str) -> dict[str, Any] | None:
    """获取用户配置"""
    client = get_api_client()
    try:
        return await client.get(f"/api/v1/config/{user_id}")
    except Exception:
        return None


def main() -> None:
    """主函数"""
    # 渲染侧边栏
    sidebar_config = render_sidebar()
    user_id = sidebar_config["user_id"]

    # 主页标题
    st.title("📊 Stock Analyzer")
    st.markdown("### 生产级智能股票分析系统")

    st.markdown("---")

    # 系统状态检查
    st.markdown("## 🔧 系统状态")

    with st.spinner("检查系统状态..."):
        try:
            health = asyncio.run(fetch_health_status())
            if health.get("status") == "healthy":
                st.success("✅ 后端服务正常")
                st.session_state.system_status = "healthy"
            else:
                st.warning("⚠️ 后端服务异常")
                st.session_state.system_status = "unhealthy"
        except Exception as e:
            st.error(f"❌ 无法连接后端服务: {e}")
            st.session_state.system_status = "unreachable"

    st.markdown("---")

    # 快速分析
    st.markdown("## 🚀 快速分析")

    col1, col2 = st.columns([2, 1])

    with col1:
        stock_code = st.text_input(
            "股票代码",
            placeholder="例如: 600519.SH",
            key="quick_stock_code",
        )

    with col2:
        analysis_type = st.selectbox(
            "分析类型",
            options=["both", "fundamental", "technical"],
            format_func=lambda x: {
                "both": "综合分析",
                "fundamental": "基本面分析",
                "technical": "技术面分析",
            }[x],
            key="quick_analysis_type",
        )

    if st.button("开始分析", type="primary", key="quick_analyze"):
        if stock_code:
            # 跳转到分析页面
            st.session_state.quick_analyze_code = stock_code
            st.session_state.quick_analyze_type = analysis_type
            st.switch_page("pages/1_📊_分析.py")
        else:
            st.warning("请输入股票代码")

    st.markdown("---")

    # 功能介绍
    st.markdown("## 📋 功能介绍")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📊 股票分析")
        st.markdown(
            """
        - 支持A股/港股
        - 多维度分析
        - 技术指标可视化
        - AI 智能分析
        """
        )

    with col2:
        st.markdown("### ⚙️ AI 配置")
        st.markdown(
            """
        - OpenAI API 配置
        - Anthropic API 配置
        - 自定义模型选择
        - 加密存储
        """
        )

    with col3:
        st.markdown("### 📋 历史记录")
        st.markdown(
            """
        - 分析历史查询
        - 报告在线查看
        - 数据导出
        - 趋势分析
        """
        )

    st.markdown("---")

    # 用户配置检查
    st.markdown("## ⚙️ 配置状态")

    with st.spinner("检查用户配置..."):
        try:
            config = asyncio.run(fetch_user_config(user_id))
            if config:
                has_openai = bool(config.get("openai_api_key"))
                has_anthropic = bool(config.get("anthropic_api_key"))

                col1, col2 = st.columns(2)
                with col1:
                    if has_openai:
                        st.success("✅ OpenAI 已配置")
                    else:
                        st.info("⚠️ OpenAI 未配置")

                with col2:
                    if has_anthropic:
                        st.success("✅ Anthropic 已配置")
                    else:
                        st.info("⚠️ Anthropic 未配置")

                if not (has_openai or has_anthropic):
                    st.markdown("👉 [前往配置页面](/配置) 设置 AI 服务")
            else:
                st.info("暂无用户配置，请前往 [配置页面](/配置) 进行设置")
        except Exception as e:
            st.warning(f"获取配置失败: {e}")

    st.markdown("---")

    # 页脚
    st.markdown(
        """
    ---
    <div style='text-align: center; color: gray;'>
        Stock Analyzer v1.1.0 | Powered by FastAPI + Streamlit
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
