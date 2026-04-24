import sys

"""CLI基本分析流程集成测试 — 用户场景: 命令行输入 → 分析执行 → 报告输出"""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
class TestCLIBasic:
    """CLI基本分析流程集成测试"""

    def test_cli_basic_analysis(self, test_output_dir):
        """完整CLI分析流程: 输入股票代码 → 执行分析 → 生成报告"""
        output_dir = test_output_dir / "cli_output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 清理之前的输出
        for f in output_dir.glob("*"):
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                import shutil

                shutil.rmtree(f)

        # 执行CLI命令（真实调用，不Mock）
        result = subprocess.run(
            [
                sys.executable,
                "stock_analyzer.py",
                "688981.SH",  # 中芯国际，数据稳定
                "--output",
                "markdown",
                "--output-dir",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=120,  # 2分钟超时（真实API调用需要时间）
        )

        # 验证命令成功执行
        assert result.returncode == 0, f"CLI执行失败: {result.stderr}"

        # 验证输出报告存在
        report_files = list(output_dir.glob("688981.SH/*.md"))
        assert len(report_files) > 0, "报告文件未生成"

        # 验证报告内容合理
        content = report_files[0].read_text()
        assert "688981.SH" in content, "报告应包含股票代码"
        assert "分析" in content or "Analysis" in content, "报告应包含分析内容"

    def test_cli_help(self):
        """帮助信息输出"""
        result = subprocess.run(
            [sys.executable, "stock_analyzer.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Stock Analyzer" in result.stdout
        assert "--type" in result.stdout
        assert "--output" in result.stdout
