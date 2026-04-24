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
        quotes = asyncio.run(datahub.fetch_daily("688981.SH"))
        financial = asyncio.run(datahub.fetch_financial("688981.SH"))

        # 组装分析结果数据
        analysis_result = {
            "stock_code": "688981.SH",
            "stock_name": "中芯国际",
            "report_date": "2026-04-24",
            "summary": f"获取到 {len(quotes)} 条日线数据，{len(financial)} 条财务数据",
            "scores": {
                "技术面": 75,
                "基本面": 80,
            },
            "recommendation": {
                "action": "HOLD",
                "confidence": 0.65,
                "reason": "数据获取成功，测试报告生成",
            },
            "technical_analysis": {
                "indicators": {
                    "最新收盘价": quotes["close"].iloc[-1] if len(quotes) > 0 else "N/A",
                    "最新成交量": quotes["volume"].iloc[-1] if len(quotes) > 0 else "N/A",
                },
            },
            "risks": ["测试数据，不构成投资建议"],
        }

        # 生成报告
        plugin = MarkdownReportPlugin()
        report_path = test_output_dir / "integration_report.md"

        # 使用 render_to_file 写入文件
        plugin.render_to_file(
            analysis_result=analysis_result,
            output_path=str(report_path),
        )

        # 验证报告生成
        assert report_path.exists()
        content = report_path.read_text()
        assert "688981.SH" in content
