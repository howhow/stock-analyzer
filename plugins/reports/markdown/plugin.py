"""
Markdown 报告插件

生成结构化的 Markdown 格式报告。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from structlog import get_logger

from framework.interfaces.report import ReportInterface

logger = get_logger(__name__)


class MarkdownReportPlugin(ReportInterface):
    """
    Markdown 报告插件

    生成结构化的 Markdown 格式报告。
    """

    def __init__(self, template_dir: str = "./templates/reports"):
        """
        初始化 Markdown 报告插件

        Args:
            template_dir: 模板目录
        """
        self._template_dir = Path(template_dir)

    @property
    def name(self) -> str:
        """报告格式名称"""
        return "markdown"

    @property
    def file_extension(self) -> str:
        """文件扩展名"""
        return ".md"

    @property
    def content_type(self) -> str:
        """MIME 类型"""
        return "text/markdown"

    def generate(
        self,
        analysis_result: Any,
        template: str | None = None,
        **kwargs,
    ) -> str:
        """
        生成 Markdown 报告

        Args:
            analysis_result: 分析结果
            template: 模板名称（可选）
            **kwargs: 额外参数

        Returns:
            Markdown 报告内容
        """
        # 提取分析结果数据
        data = self._extract_data(analysis_result)

        # 生成报告各部分
        sections = [
            self._generate_header(data),
            self._generate_summary(data),
            self._generate_scores(data),
            self._generate_recommendation(data),
            self._generate_technical_analysis(data),
            self._generate_risks(data),
            self._generate_opportunities(data),
            self._generate_trading_advice(data),
            self._generate_footer(data),
        ]

        return "\n\n".join(filter(None, sections))

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
        content = self.generate(analysis_result, template, **kwargs)

        # 确保输出路径有正确扩展名
        output_file = Path(output_path)
        if output_file.suffix != self.file_extension:
            output_file = output_file.with_suffix(self.file_extension)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding="utf-8")

        logger.info("markdown_report_rendered", path=str(output_file))
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

    def _generate_header(self, data: dict[str, Any]) -> str:
        """生成报告头部"""
        stock_code = data.get("stock_code", "未知")
        stock_name = data.get("stock_name", "")
        report_date = data.get("report_date", datetime.now().strftime("%Y-%m-%d"))

        title = f"# 📊 {stock_code} 分析报告"
        if stock_name:
            title += f" - {stock_name}"

        return f"""{title}

> 生成日期: {report_date}
> 数据源: {data.get('data_source', 'Stock Analyzer')}"""

    def _generate_summary(self, data: dict[str, Any]) -> str:
        """生成摘要"""
        summary = data.get("summary", data.get("details", {}).get("summary", ""))
        if not summary:
            return ""

        return f"""## 📝 分析摘要

{summary}"""

    def _generate_scores(self, data: dict[str, Any]) -> str:
        """生成评分部分"""
        scores = data.get("scores", {})
        if not scores:
            return ""

        lines = ["## 📈 评分指标", ""]

        for metric, value in scores.items():
            if isinstance(value, (int, float)):
                bar = "█" * int(value / 10) + "░" * (10 - int(value / 10))
                lines.append(f"- **{metric}**: {value}/100 {bar}")

        return "\n".join(lines)

    def _generate_recommendation(self, data: dict[str, Any]) -> str:
        """生成建议部分"""
        recommendation = data.get(
            "recommendation", data.get("details", {}).get("recommendation")
        )
        if not recommendation:
            return ""

        action = recommendation.get("action", "HOLD")
        confidence = recommendation.get("confidence", 0)
        reason = recommendation.get("reason", "")

        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(action, "⚪")

        return f"""## 💡 操作建议

{emoji} **{action}** (置信度: {confidence:.0%})

{reason}"""

    def _generate_technical_analysis(self, data: dict[str, Any]) -> str:
        """生成技术分析"""
        technical = data.get(
            "technical_analysis", data.get("details", {}).get("technical", {})
        )
        if not technical:
            return ""

        lines = ["## 📉 技术分析", ""]

        indicators = technical.get("indicators", {})
        for name, value in indicators.items():
            lines.append(f"- **{name}**: {value}")

        return "\n".join(lines)

    def _generate_risks(self, data: dict[str, Any]) -> str:
        """生成风险提示"""
        risks = data.get("risks", data.get("details", {}).get("risks", []))
        if not risks:
            return ""

        lines = ["## ⚠️ 风险提示", ""]
        for risk in risks:
            lines.append(f"- {risk}")

        return "\n".join(lines)

    def _generate_opportunities(self, data: dict[str, Any]) -> str:
        """生成机会分析"""
        opportunities = data.get(
            "opportunities", data.get("details", {}).get("opportunities", [])
        )
        if not opportunities:
            return ""

        lines = ["## 🎯 投资机会", ""]
        for opp in opportunities:
            lines.append(f"- {opp}")

        return "\n".join(lines)

    def _generate_trading_advice(self, data: dict[str, Any]) -> str:
        """生成交易建议"""
        advice = data.get(
            "trading_advice", data.get("details", {}).get("trading_advice", {})
        )
        if not advice:
            return ""

        lines = ["## 💰 交易建议", ""]

        if advice.get("entry_price"):
            lines.append(f"- **建议入场价**: {advice['entry_price']}")
        if advice.get("stop_loss"):
            lines.append(f"- **止损位**: {advice['stop_loss']}")
        if advice.get("target_price"):
            lines.append(f"- **目标价**: {advice['target_price']}")

        return "\n".join(lines)

    def _generate_footer(self, data: dict[str, Any]) -> str:
        """生成报告尾部"""
        return """---

*本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。*

---
*Generated by Stock Analyzer*
"""
