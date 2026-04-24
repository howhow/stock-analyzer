"""Markdown报告生成集成测试"""

from pathlib import Path

import pytest


@pytest.mark.integration
class TestMarkdownReportIntegration:
    """Markdown报告生成集成测试"""

    def test_report_generation(self, datahub, test_output_dir):
        """生成真实分析报告"""
        import asyncio

        from plugins.reports.markdown.plugin import MarkdownReportPlugin

        # 获取真实数据
        quotes = asyncio.run(datahub.fetch_daily_quotes("688981.SH"))
        financial = asyncio.run(datahub.fetch_financial("688981.SH"))

        # 生成报告
        plugin = MarkdownReportPlugin()
        report_path = test_output_dir / "integration_report.md"

        plugin.generate(
            symbol="688981.SH",
            quotes=quotes,
            financial=financial,
            output_path=report_path,
        )

        # 验证报告生成
        assert report_path.exists()
        content = report_path.read_text()
        assert "688981.SH" in content
