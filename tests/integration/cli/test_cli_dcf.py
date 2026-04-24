import sys

"""CLI DCF估值分析集成测试"""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
class TestCLIDCF:
    """CLI DCF估值分析集成测试"""

    def test_cli_dcf_analysis(self, test_output_dir):
        """DCF估值分析流程"""
        output_dir = test_output_dir / "cli_dcf_output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 清理之前的输出
        for f in output_dir.glob("*"):
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                import shutil

                shutil.rmtree(f)

        result = subprocess.run(
            [
                sys.executable,
                "stock_analyzer.py",
                "688981.SH",  # 中芯国际
                "--type",
                "dcf",
                "--output",
                "markdown",
                "--output-dir",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        assert result.returncode == 0, f"CLI DCF执行失败: {result.stderr}"

        # 验证报告生成
        report_files = list(output_dir.glob("688981.SH/*.md"))
        assert len(report_files) > 0, "DCF报告未生成"

        content = report_files[0].read_text()
        assert "DCF" in content or "估值" in content
