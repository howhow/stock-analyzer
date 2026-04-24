"""CLI报告输出验证集成测试"""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
class TestCLIOutput:
    """CLI报告输出验证集成测试"""

    def test_cli_html_output(self, test_output_dir):
        """HTML报告输出验证"""
        output_dir = test_output_dir / "cli_html_output"
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
                "python",
                "stock_analyzer.py",
                "688981.SH",
                "--output",
                "html",
                "--output-dir",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        assert result.returncode == 0, f"CLI HTML输出失败: {result.stderr}"

        # 验证HTML报告生成
        report_files = list(output_dir.glob("688981.SH/*.html"))
        assert len(report_files) > 0, "HTML报告未生成"

        content = report_files[0].read_text()
        assert "<html" in content or "<!DOCTYPE" in content, "应为HTML格式"
        assert "688981.SH" in content, "报告应包含股票代码"

    def test_cli_both_output(self, test_output_dir):
        """同时输出HTML和Markdown报告"""
        output_dir = test_output_dir / "cli_both_output"
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
                "python",
                "stock_analyzer.py",
                "688981.SH",
                "--output",
                "both",
                "--output-dir",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        assert result.returncode == 0, f"CLI Both输出失败: {result.stderr}"

        # 验证两种格式都生成
        html_files = list(output_dir.glob("688981.SH/*.html"))
        md_files = list(output_dir.glob("688981.SH/*.md"))
        assert len(html_files) > 0, "HTML报告未生成"
        assert len(md_files) > 0, "Markdown报告未生成"
