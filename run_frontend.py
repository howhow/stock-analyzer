#!/usr/bin/env python3
"""
Stock Analyzer Frontend 启动脚本

启动 Streamlit 前端应用
"""

import subprocess
import sys
from pathlib import Path


def check_venv() -> bool:
    """检查虚拟环境是否存在"""
    venv_path = Path("local_venv")
    return venv_path.exists() and venv_path.is_dir()


def check_streamlit() -> bool:
    """检查 Streamlit 是否已安装"""
    try:
        import streamlit
        return True
    except ImportError:
        return False


def install_streamlit() -> bool:
    """安装 Streamlit"""
    print("⚠️  Streamlit 未安装，正在安装...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "streamlit", "plotly", "-q"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def check_backend() -> bool:
    """检查后端服务是否运行"""
    try:
        import httpx
        response = httpx.get("http://localhost:8000/api/v1/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def main():
    """主函数"""
    print("🚀 Stock Analyzer Frontend")
    print("=" * 30)

    # 检查虚拟环境
    if not check_venv():
        print("❌ 虚拟环境不存在，请先运行: make venv")
        sys.exit(1)

    # 检查 Streamlit
    if not check_streamlit():
        if not install_streamlit():
            print("❌ Streamlit 安装失败")
            sys.exit(1)

    # 检查后端服务
    print("🔍 检查后端服务...")
    if not check_backend():
        print("⚠️  后端服务未启动，请先启动后端:")
        print("   make dev")
        print()
        response = input("是否继续启动前端? (y/N): ")
        if response.lower() != "y":
            sys.exit(0)

    # 设置环境变量
    import os
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    # 启动前端
    print("✅ 启动前端服务...")
    print("🌐 访问地址: http://localhost:8501")
    print("=" * 30)

    # 切换到 frontend 目录并启动 Streamlit
    frontend_dir = Path(__file__).parent / "frontend"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app.py"],
        cwd=frontend_dir
    )


if __name__ == "__main__":
    main()
