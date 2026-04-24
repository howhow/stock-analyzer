"""集成测试全局配置 — 集中加载 .env + 验证环境 + 共享 fixtures"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
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


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """显示集成测试时长统计"""
    integration_tests = [
        report
        for report in terminalreporter.stats.get("passed", [])
        if "integration" in report.nodeid
    ]

    if integration_tests:
        total_time = sum(report.duration for report in integration_tests)
        avg_time = total_time / len(integration_tests)

        terminalreporter.write_sep("=", "集成测试统计")
        terminalreporter.write_line(f"集成测试数量: {len(integration_tests)}")
        terminalreporter.write_line(f"总耗时: {total_time:.2f}s")
        terminalreporter.write_line(f"平均耗时: {avg_time:.2f}s")

        # 标记长时间测试（可能涉及真实API调用）
        slow_tests = [report for report in integration_tests if report.duration > 30]
        if slow_tests:
            terminalreporter.write_line(f"慢测试(>30s): {len(slow_tests)}个")
            for report in slow_tests:
                terminalreporter.write_line(
                    f"  - {report.nodeid}: {report.duration:.2f}s"
                )


# ═══════════════════════════════════════════════════════════════
# 共享 fixtures
# ═══════════════════════════════════════════════════════════════


def get_free_port() -> int:
    """获取一个空闲端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def test_output_dir():
    """集成测试输出目录"""
    output_dir = Path("local_test_report/integration")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture(scope="session")
def datahub():
    """真实 DataHub 实例（session 级别，通过 DataHub 调用数据源）"""
    from framework.data.hub import DataHub
    from plugins.data_sources.tushare.plugin import TusharePlugin
    from plugins.data_sources.akshare.plugin import AKSharePlugin

    # 创建数据源实例
    tushare = TusharePlugin()
    akshare = AKSharePlugin()

    hub = DataHub(sources=[tushare, akshare])
    return hub


@pytest.fixture(scope="class")
def api_service():
    """启动 API 服务（class 级别，使用随机端口）"""
    port = get_free_port()

    # 启动API服务
    api_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 等待服务就绪
    max_retries = 30
    for _ in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}/api/v1/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        api_process.terminate()
        api_process.wait(timeout=5)
        pytest.fail("API服务启动超时")

    yield {"process": api_process, "port": port}

    # 清理
    api_process.terminate()
    api_process.wait(timeout=5)


@pytest.fixture(scope="class")
def celery_worker():
    """启动 Celery Worker（class 级别）"""
    celery_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "app.tasks.celery_app",
            "worker",
            "--loglevel=info",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 等待worker启动
    time.sleep(5)

    yield celery_process

    # 清理
    celery_process.terminate()
    celery_process.wait(timeout=5)
