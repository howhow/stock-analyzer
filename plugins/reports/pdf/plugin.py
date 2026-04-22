"""
PDF 报告插件

生成专业的 PDF 格式报告。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from structlog import get_logger

from framework.interfaces.report import ReportInterface

logger = get_logger(__name__)


class PDFReportPlugin(ReportInterface):
    """
    PDF 报告插件

    基于 HTML 模板生成专业的 PDF 报告。
    """

    def __init__(
        self,
        template_dir: str = "./templates/reports",
        font_path: str | None = None,
    ):
        """
        初始化 PDF 报告插件

        Args:
            template_dir: 模板目录
            font_path: 中文字体路径（可选）
        """
        self._template_dir = Path(template_dir)
        self._font_path = font_path

    @property
    def name(self) -> str:
        """报告格式名称"""
        return "pdf"

    @property
    def file_extension(self) -> str:
        """文件扩展名"""
        return ".pdf"

    @property
    def content_type(self) -> str:
        """MIME 类型"""
        return "application/pdf"

    def generate(
        self,
        analysis_result: Any,
        template: str | None = None,
        **kwargs,
    ) -> bytes:
        """
        生成 PDF 报告

        Args:
            analysis_result: 分析结果
            template: 模板名称（可选）
            **kwargs: 额外参数

        Returns:
            PDF 报告二进制内容
        """
        # 提取数据
        data = self._extract_data(analysis_result)

        # 生成 HTML
        html_content = self._generate_html(data, template)

        # 转换为 PDF
        pdf_bytes = self._html_to_pdf(html_content)

        return pdf_bytes

    def render_to_file(
        self,
        analysis_result: Any,
        output_path: str,
        template: str | None = None,
        **kwargs,
    ) -> str:
        """
        渲染报告到文件

        Args:
            analysis_result: 分析结果
            output_path: 输出路径
            template: 模板名称（可选）
            **kwargs: 额外参数

        Returns:
            生成的文件路径
        """
        pdf_bytes = self.generate(analysis_result, template, **kwargs)

        # 确保输出路径有正确扩展名
        output_file = Path(output_path)
        if output_file.suffix != self.file_extension:
            output_file = output_file.with_suffix(self.file_extension)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(pdf_bytes)

        logger.info("pdf_report_rendered", path=str(output_file))
        return str(output_file)

    def _extract_data(self, analysis_result: Any) -> dict[str, Any]:
        """从分析结果提取数据"""
        if hasattr(analysis_result, "model_dump"):
            extracted1: dict[str, Any] = analysis_result.model_dump()
            return extracted1
        elif hasattr(analysis_result, "dict"):
            extracted2: dict[str, Any] = analysis_result.dict()
            return extracted2
        elif isinstance(analysis_result, dict):
            return analysis_result
        else:
            return {"raw_result": str(analysis_result)}

    def _generate_html(self, data: dict[str, Any], template: str | None) -> str:
        """生成 HTML 内容"""
        stock_code = data.get("stock_code", "未知")
        stock_name = data.get("stock_name", "")
        report_date = data.get("report_date", datetime.now().strftime("%Y-%m-%d"))

        # 简单的 HTML 模板
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{stock_code} 分析报告</title>
    <style>
        body {{
            font-family: "SimSun", "微软雅黑", Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 10px;
            margin-top: 30px;
        }}
        .header {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .score {{
            background: #e8f4f8;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .recommendation {{
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .buy {{ background: #d4edda; }}
        .sell {{ background: #f8d7da; }}
        .hold {{ background: #fff3cd; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background: #f2f2f2;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #666;
            text-align: center;
        }}
        .warning {{
            color: #856404;
            background: #fff3cd;
            padding: 10px;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <h1>📊 {stock_code} 分析报告</h1>
    {"<h3>" + stock_name + "</h3>" if stock_name else ""}

    <div class="header">
        <p><strong>生成日期:</strong> {report_date}</p>
        <p><strong>数据源:</strong> {data.get('data_source', 'Stock Analyzer')}</p>
    </div>

    {self._generate_summary_html(data)}
    {self._generate_scores_html(data)}
    {self._generate_recommendation_html(data)}
    {self._generate_technical_html(data)}
    {self._generate_risks_html(data)}
    {self._generate_opportunities_html(data)}

    <div class="footer">
        <p class="warning">⚠️ 本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
        <p>Generated by Stock Analyzer</p>
    </div>
</body>
</html>"""
        return html

    def _generate_summary_html(self, data: dict[str, Any]) -> str:
        """生成摘要 HTML"""
        summary = data.get("summary", data.get("details", {}).get("summary", ""))
        if not summary:
            return ""
        return f"""<h2>📝 分析摘要</h2>
    <p>{summary}</p>"""

    def _generate_scores_html(self, data: dict[str, Any]) -> str:
        """生成评分 HTML"""
        scores = data.get("scores", {})
        if not scores:
            return ""

        rows = []
        for metric, value in scores.items():
            if isinstance(value, (int, float)):
                rows.append(f"<tr><td>{metric}</td><td>{value}/100</td></tr>")

        if not rows:
            return ""

        return f"""<h2>📈 评分指标</h2>
    <table>
        <tr><th>指标</th><th>得分</th></tr>
        {"".join(rows)}
    </table>"""

    def _generate_recommendation_html(self, data: dict[str, Any]) -> str:
        """生成建议 HTML"""
        recommendation = data.get(
            "recommendation", data.get("details", {}).get("recommendation")
        )
        if not recommendation:
            return ""

        action = recommendation.get("action", "HOLD")
        confidence = recommendation.get("confidence", 0)
        reason = recommendation.get("reason", "")

        css_class = {"BUY": "buy", "SELL": "sell", "HOLD": "hold"}.get(action, "hold")

        return f"""<h2>💡 操作建议</h2>
    <div class="recommendation {css_class}">
        <h3>{action} (置信度: {confidence:.0%})</h3>
        <p>{reason}</p>
    </div>"""

    def _generate_technical_html(self, data: dict[str, Any]) -> str:
        """生成技术分析 HTML"""
        technical = data.get(
            "technical_analysis", data.get("details", {}).get("technical", {})
        )
        if not technical:
            return ""

        indicators = technical.get("indicators", {})
        if not indicators:
            return ""

        rows = [f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in indicators.items()]

        return f"""<h2>📉 技术分析</h2>
    <table>
        <tr><th>指标</th><th>值</th></tr>
        {"".join(rows)}
    </table>"""

    def _generate_risks_html(self, data: dict[str, Any]) -> str:
        """生成风险提示 HTML"""
        risks = data.get("risks", data.get("details", {}).get("risks", []))
        if not risks:
            return ""

        items = "".join(f"<li>{r}</li>" for r in risks)
        return f"""<h2>⚠️ 风险提示</h2>
    <ul>{items}</ul>"""

    def _generate_opportunities_html(self, data: dict[str, Any]) -> str:
        """生成机会分析 HTML"""
        opportunities = data.get(
            "opportunities", data.get("details", {}).get("opportunities", [])
        )
        if not opportunities:
            return ""

        items = "".join(f"<li>{o}</li>" for o in opportunities)
        return f"""<h2>🎯 投资机会</h2>
    <ul>{items}</ul>"""

    def _html_to_pdf(self, html_content: str) -> bytes:
        """将 HTML 转换为 PDF"""
        try:
            # 尝试使用 weasyprint
            from weasyprint import HTML

            pdf_bytes: bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes

        except ImportError:
            # 回退到简单的文本报告
            logger.warning("weasyprint_not_available", fallback="text")
            return self._generate_fallback_pdf(html_content)

    def _generate_fallback_pdf(self, html_content: str) -> bytes:
        """生成回退 PDF（纯文本）"""
        # 简单的文本报告作为回退
        text = html_content.replace("<", "\n<").replace(">", ">\n")
        return text.encode("utf-8")
