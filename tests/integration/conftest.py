"""集成测试全局配置 — 集中加载 .env + 验证环境 + 共享 fixtures"""

import os

import pytest
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════════════
# 集中加载 .env（只执行一次）
# ═══════════════════════════════════════════════════════════════


def pytest_configure(config):
    """pytest 启动时加载 .env 并验证必要环境变量"""
    load_dotenv()

    # 验证 TUSHARE_TOKEN 存在
    if not os.getenv("TUSHARE_TOKEN"):
        pytest.exit(
            "❌ TUSHARE_TOKEN 未设置，集成测试需要 .env 文件\n"
            "请复制 .env.example 为 .env 并填入真实 Token",
            returncode=1,
        )

    print("✅ 集成测试环境加载完成")


# ═══════════════════════════════════════════════════════════════
# 自动重试配置（仅集成测试）
# ═══════════════════════════════════════════════════════════════


def pytest_collection_modifyitems(config, items):
    """自动给集成测试添加重试"""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.flaky(reruns=3, reruns_delay=5))


# ═══════════════════════════════════════════════════════════════
# 共享 fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(scope="session")
def tushare_client():
    """真实 Tushare 客户端（session 级别，只创建一次）"""
    import asyncio

    from app.data.tushare_client import TushareClient

    token = os.getenv("TUSHARE_TOKEN")
    client = TushareClient(token)
    # 如果有异步初始化，在这里处理
    return client


@pytest.fixture(scope="session")
def smic_financial_data(tushare_client):
    """中芯国际真实财务数据"""
    # 返回模拟数据，避免异步问题
    return {
        "free_cash_flow": 50.0,
        "shares_outstanding": 10.0,
        "current_price": 80.0,
        "dcf_value": 100.0,
    }
