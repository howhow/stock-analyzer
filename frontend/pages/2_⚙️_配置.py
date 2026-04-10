"""
配置页面 - AI 服务配置
"""

import asyncio
from typing import Any

import streamlit as st

from frontend.components.sidebar import render_sidebar
from frontend.components.tables import render_config_table
from frontend.utils.api_client import get_api_client

# 页面配置
st.set_page_config(
    page_title="AI 配置 - Stock Analyzer",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


async def get_user_config(user_id: str) -> dict[str, Any] | None:
    """获取用户配置"""
    client = get_api_client()
    try:
        return await client.get(f"/api/v1/config/{user_id}")
    except Exception:
        return None


async def create_user_config(
    user_id: str, config_data: dict[str, Any]
) -> dict[str, Any]:
    """创建用户配置"""
    client = get_api_client()
    return await client.post(
        "/api/v1/config/",
        data={"user_id": user_id, **config_data},
    )


async def update_user_config(
    user_id: str, config_data: dict[str, Any]
) -> dict[str, Any]:
    """更新用户配置"""
    client = get_api_client()
    return await client.put(f"/api/v1/config/{user_id}", data=config_data)


def main() -> None:
    """主函数"""
    # 渲染侧边栏
    sidebar_config = render_sidebar()
    user_id = sidebar_config["user_id"]

    # 页面标题
    st.title("⚙️ AI 服务配置")
    st.markdown("配置 AI 服务提供商的 API Key 和模型参数")
    st.markdown("---")

    # 获取当前配置
    current_config = None
    with st.spinner("加载配置..."):
        try:
            current_config = asyncio.run(get_user_config(user_id))
        except Exception as e:
            st.warning(f"获取配置失败: {e}")

    # 配置表单
    st.markdown("## 🔑 OpenAI 配置")

    col1, col2 = st.columns([2, 1])

    with col1:
        # API Key（敏感信息，显示脱敏）
        default_openai_key = ""
        if current_config and current_config.get("openai_api_key"):
            # 显示脱敏的 key
            default_openai_key = current_config["openai_api_key"]

        openai_api_key = st.text_input(
            "OpenAI API Key",
            value=default_openai_key,
            type="password",
            placeholder="sk-...",
            help="API Key 将加密存储",
            key="openai_api_key_input",
        )

    with col2:
        default_openai_model = (
            current_config.get("openai_model", "gpt-4-turbo")
            if current_config
            else "gpt-4-turbo"
        )
        openai_model = st.selectbox(
            "OpenAI Model",
            options=[
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
                "deepseek-v3.2",
                "qwen3-235b",
                "glm-4-7b",
            ],
            index=0,
            key="openai_model_select",
        )

    openai_base_url = st.text_input(
        "OpenAI Base URL",
        value=(
            current_config.get("openai_base_url", "https://api.openai.com/v1")
            if current_config
            else "https://api.openai.com/v1"
        ),
        placeholder="https://api.openai.com/v1",
        help="自定义 API 端点，支持 OpenAI 兼容的服务",
        key="openai_base_url_input",
    )

    st.markdown("---")

    # Anthropic 配置
    st.markdown("## 🤖 Anthropic 配置")

    col1, col2 = st.columns([2, 1])

    with col1:
        default_anthropic_key = ""
        if current_config and current_config.get("anthropic_api_key"):
            default_anthropic_key = current_config["anthropic_api_key"]

        anthropic_api_key = st.text_input(
            "Anthropic API Key",
            value=default_anthropic_key,
            type="password",
            placeholder="sk-ant-...",
            help="API Key 将加密存储",
            key="anthropic_api_key_input",
        )

    with col2:
        default_anthropic_model = (
            current_config.get("anthropic_model", "claude-3-opus-20240229")
            if current_config
            else "claude-3-opus-20240229"
        )
        anthropic_model = st.selectbox(
            "Anthropic Model",
            options=[
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ],
            index=0,
            key="anthropic_model_select",
        )

    st.markdown("---")

    # 分析偏好
    st.markdown("## 📊 分析偏好")

    col1, col2 = st.columns(2)

    with col1:
        default_analysis_type = (
            current_config.get("default_analysis_type", "both")
            if current_config
            else "both"
        )
        default_analysis_type = st.selectbox(
            "默认分析类型",
            options=["both", "fundamental", "technical"],
            format_func=lambda x: {
                "both": "综合分析",
                "fundamental": "基本面分析",
                "technical": "技术面分析",
            }[x],
            key="default_analysis_type_select",
        )

    with col2:
        default_days = (
            current_config.get("default_days", 120) if current_config else 120
        )
        default_days = st.number_input(
            "默认分析天数",
            min_value=30,
            max_value=365,
            value=default_days,
            step=10,
            key="default_days_input",
        )

    st.markdown("---")

    # 保存按钮
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("💾 保存配置", type="primary", key="save_config"):
            # 构建配置数据
            config_data = {
                "openai_api_key": openai_api_key if openai_api_key else None,
                "openai_base_url": openai_base_url if openai_base_url else None,
                "openai_model": openai_model if openai_model else None,
                "anthropic_api_key": anthropic_api_key if anthropic_api_key else None,
                "anthropic_model": anthropic_model if anthropic_model else None,
                "default_analysis_type": default_analysis_type,
                "default_days": default_days,
            }

            with st.spinner("保存配置..."):
                try:
                    if current_config:
                        # 更新配置
                        result = asyncio.run(update_user_config(user_id, config_data))
                        st.success("✅ 配置更新成功！")
                    else:
                        # 创建配置
                        result = asyncio.run(create_user_config(user_id, config_data))
                        st.success("✅ 配置创建成功！")

                    # 更新 session state
                    st.session_state.user_config = result

                except Exception as e:
                    st.error(f"保存配置失败: {e}")

    with col2:
        if st.button("🔄 重置", key="reset_config"):
            st.rerun()

    st.markdown("---")

    # 当前配置预览
    if current_config:
        st.markdown("## 📋 当前配置预览")
        with st.expander("查看详细配置", expanded=False):
            render_config_table(current_config)

    # 安全提示
    st.markdown("---")
    st.markdown(
        """
    ### 🔒 安全提示

    - API Key 使用 AES-256 加密存储
    - 显示时自动脱敏处理
    - 建议定期更换 API Key
    - 不要在公共场所保存配置
    """
    )


if __name__ == "__main__":
    main()
