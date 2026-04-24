"""端到端分析流程集成测试 — 完整用户场景"""

import subprocess
import time

import pytest
import requests


@pytest.mark.integration
class TestEndToEndAnalysis:
    """端到端分析流程集成测试"""

    def test_cli_end_to_end(self, test_output_dir):
        """CLI完整流程: 输入 → 分析 → 报告"""
        output_dir = test_output_dir / "e2e_cli"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 清理
        for f in output_dir.glob("*"):
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                import shutil

                shutil.rmtree(f)

        # 执行完整分析
        result = subprocess.run(
            [
                "python",
                "stock_analyzer.py",
                "688981.SH",
                "--type",
                "full",
                "--output",
                "both",
                "--output-dir",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5分钟超时
        )

        assert result.returncode == 0, f"端到端CLI失败: {result.stderr}"

        # 验证报告生成
        html_files = list(output_dir.glob("688981.SH/*.html"))
        md_files = list(output_dir.glob("688981.SH/*.md"))
        assert len(html_files) > 0, "HTML报告未生成"
        assert len(md_files) > 0, "Markdown报告未生成"

        # 验证报告内容包含框架级分析
        md_content = md_files[0].read_text()
        assert "DCF" in md_content or "估值" in md_content
        assert "四季" in md_content or "Season" in md_content
        assert "五行" in md_content or "Wuxing" in md_content

    def test_api_end_to_end(self, api_service, test_output_dir):
        """API完整流程: 请求 → 分析 → 结果"""
        # 发送分析请求
        response = requests.get(
            "http://localhost:8000/api/v1/analysis/688981.SH",
            timeout=120,
        )
        assert response.status_code in [200, 202]

        if response.status_code == 202:
            # 异步任务，轮询结果
            task_id = response.json().get("task_id")
            if task_id:
                max_retries = 30
                for _ in range(max_retries):
                    time.sleep(2)
                    status_response = requests.get(
                        f"http://localhost:8000/api/v1/tasks/{task_id}",
                        timeout=10,
                    )
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") == "completed":
                            break
                else:
                    pytest.fail("异步任务执行超时")
