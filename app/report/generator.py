"""
报告生成器

基于 Jinja2 模板生成 HTML 分析报告
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.analysis import AnalysisResult
from app.models.report import (
    ReportContent,
    ReportFormat,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """
    报告生成器

    基于 Jinja2 模板生成 HTML 分析报告
    """

    def __init__(self, template_dir: Path | None = None):
        """
        初始化报告生成器

        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = template_dir or Path(__file__).parent / "templates"

        # 确保 templates 目录存在
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 Jinja2 环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 生成器版本
        self.version = "1.0.0"

        logger.info("report_generator_initialized", template_dir=str(self.template_dir))

    def generate(
        self,
        analysis_result: AnalysisResult,
        format_type: ReportFormat = ReportFormat.HTML,
    ) -> ReportContent:
        """
        生成分析报告

        Args:
            analysis_result: 分析结果
            format_type: 报告格式

        Returns:
            报告内容
        """
        report_id = self._generate_report_id()

        logger.info(
            "report_generation_started",
            report_id=report_id,
            stock_code=analysis_result.stock_code,
            format=format_type.value,
        )

        try:
            # 准备报告数据
            report_data = self._prepare_report_data(analysis_result)

            # 生成报告内容
            if format_type == ReportFormat.HTML:
                content = self._generate_html(report_data)
            elif format_type == ReportFormat.JSON:
                content = self._generate_json(report_data)
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            report_content = ReportContent(
                report_id=report_id,
                stock_code=analysis_result.stock_code,
                stock_name=analysis_result.stock_name,
                analysis_data=report_data,
                generator_version=self.version,
            )

            logger.info(
                "report_generation_completed",
                report_id=report_id,
                stock_code=analysis_result.stock_code,
                content_length=len(content),
            )

            return report_content

        except Exception as e:
            logger.error(
                "report_generation_failed",
                report_id=report_id,
                stock_code=analysis_result.stock_code,
                error=str(e),
            )
            raise

    def _generate_report_id(self) -> str:
        """生成报告ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"rpt_{timestamp}_{unique_id}"

    def _prepare_report_data(self, result: AnalysisResult) -> dict[str, Any]:
        """
        准备报告数据

        Args:
            result: 分析结果

        Returns:
            报告数据字典
        """
        analyst = result.analyst_report
        trader = result.trader_signal

        # 评分数据
        scores = {
            "total": analyst.total_score,
            "fundamental": analyst.fundamental_score,
            "technical": analyst.technical_score,
            "signal_strength": analyst.dimension_scores.signal_strength,
            "opportunity_quality": analyst.dimension_scores.opportunity_quality,
            "risk_level": analyst.dimension_scores.risk_level,
        }

        # 风险评估
        risk_assessment = self._calculate_risk_assessment(
            analyst.dimension_scores.risk_level, trader.var_95, trader.max_drawdown
        )

        # 时机建议
        timing_advice = self._generate_timing_advice(
            trader.entry_timing, trader.entry_price, trader.stop_loss_price
        )

        return {
            # 基本信息
            "stock_code": result.stock_code,
            "stock_name": result.stock_name,
            "analysis_id": result.analysis_id,
            "analysis_type": result.analysis_type.value,
            "mode": result.mode.value,
            "generated_at": datetime.now().isoformat(),
            # 评分
            "scores": scores,
            "score_grade": self._get_score_grade(analyst.total_score),
            # 分析结论
            "recommendation": trader.recommendation.value,
            "confidence": trader.confidence,
            "wyckoff_phase": analyst.wyckoff_phase.value,
            "mtf_alignment": trader.mtf_alignment.value,
            "entry_timing": trader.entry_timing.value,
            # 价格信息
            "support_levels": analyst.support_levels,
            "resistance_levels": analyst.resistance_levels,
            "entry_price": trader.entry_price,
            "stop_loss_price": trader.stop_loss_price,
            "target_price": trader.target_price,
            "expected_return": trader.expected_return,
            # 风险评估
            "risk_assessment": risk_assessment,
            "var_95": trader.var_95,
            "max_drawdown": trader.max_drawdown,
            # 时机建议
            "timing_advice": timing_advice,
        }

    def _calculate_risk_assessment(
        self,
        risk_level: float,
        var_95: float | None,
        max_drawdown: float | None,
    ) -> str:
        """计算风险评估描述"""
        if risk_level >= 4:
            base = "低风险"
        elif risk_level >= 3:
            base = "中等风险"
        elif risk_level >= 2:
            base = "较高风险"
        else:
            base = "高风险"

        details = []
        if var_95 is not None:
            details.append(f"VaR(95%)={var_95:.2f}%")
        if max_drawdown is not None:
            details.append(f"最大回撤={max_drawdown:.2f}%")

        if details:
            return f"{base} ({', '.join(details)})"
        return base

    def _generate_timing_advice(
        self,
        entry_timing: str,
        entry_price: float | None,
        stop_loss: float | None,
    ) -> str:
        """生成时机建议"""
        if entry_timing == "immediate":
            advice = "建议立即入场"
            if entry_price:
                advice += f"，参考价格 {entry_price:.2f}"
            if stop_loss:
                advice += f"，止损位 {stop_loss:.2f}"
        elif entry_timing == "wait":
            advice = "建议等待更好时机"
        else:
            advice = "建议暂时回避"

        return advice

    def _get_score_grade(self, score: float) -> str:
        """获取评分等级"""
        if score >= 4.5:
            return "A+ (优秀)"
        elif score >= 4.0:
            return "A (良好)"
        elif score >= 3.5:
            return "B+ (较好)"
        elif score >= 3.0:
            return "B (一般)"
        elif score >= 2.5:
            return "C+ (较弱)"
        elif score >= 2.0:
            return "C (较差)"
        else:
            return "D (不建议)"

    def _generate_html(self, data: dict[str, Any]) -> str:
        """
        生成 HTML 报告

        Args:
            data: 报告数据

        Returns:
            HTML 内容
        """
        try:
            template = self.env.get_template("report.html")
            return template.render(**data)
        except Exception:
            # 如果模板不存在，使用内置模板
            return self._generate_fallback_html(data)

    def _generate_fallback_html(self, data: dict[str, Any]) -> str:
        """生成后备 HTML（无模板时使用）"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票分析报告 - {data['stock_code']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #1890ff;
            padding-bottom: 16px;
        }}
        .stock-code {{
            font-size: 24px;
            font-weight: bold;
            color: #1890ff;
        }}
        .stock-name {{
            font-size: 16px;
            color: #666;
        }}
        .score-section {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}
        .score-item {{
            text-align: center;
            padding: 16px;
            background: #f9f9f9;
            border-radius: 8px;
        }}
        .score-value {{
            font-size: 32px;
            font-weight: bold;
            color: #1890ff;
        }}
        .score-label {{
            font-size: 12px;
            color: #999;
        }}
        .recommendation {{
            font-size: 18px;
            font-weight: bold;
            padding: 12px;
            text-align: center;
            border-radius: 8px;
            margin: 16px 0;
        }}
        .buy {{ background: #f6ffed; color: #52c41a; }}
        .hold {{ background: #fffbe6; color: #faad14; }}
        .sell {{ background: #fff2f0; color: #ff4d4f; }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .info-label {{ color: #999; }}
        .info-value {{ font-weight: 500; }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="card header">
        <div class="stock-code">{data['stock_code']}</div>
        <div class="stock-name">{data.get('stock_name', '')}</div>
        <div style="margin-top: 8px; color: #999; font-size: 12px;">
            生成时间: {data['generated_at']}
        </div>
    </div>

    <div class="card">
        <h3>综合评分</h3>
        <div class="score-section">
            <div class="score-item">
                <div class="score-value">{data['scores']['total']:.1f}</div>
                <div class="score-label">综合评分</div>
            </div>
            <div class="score-item">
                <div class="score-value">{data['scores']['signal_strength']:.1f}</div>
                <div class="score-label">信号强度</div>
            </div>
            <div class="score-item">
                <div class="score-value">{data['scores']['risk_level']:.1f}</div>
                <div class="score-label">安全等级</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 16px;">
            <span style="font-size: 14px; color: #666;">评级: {data['score_grade']}</span>
        </div>
    </div>

    <div class="card">
        <h3>投资建议</h3>
        <div class="recommendation {'buy' if '买入' in data['recommendation'] else 'hold' if '持有' in data['recommendation'] else 'sell'}">
            {data['recommendation']}
        </div>
        <div style="text-align: center; color: #666;">
            置信度: {data['confidence']:.0f}%
        </div>
    </div>

    <div class="card">
        <h3>分析详情</h3>
        <div class="info-row">
            <span class="info-label">威科夫阶段</span>
            <span class="info-value">{data['wyckoff_phase']}</span>
        </div>
        <div class="info-row">
            <span class="info-label">多周期对齐</span>
            <span class="info-value">{data['mtf_alignment']}</span>
        </div>
        <div class="info-row">
            <span class="info-label">入场时机</span>
            <span class="info-value">{data['entry_timing']}</span>
        </div>
        <div class="info-row">
            <span class="info-label">风险评估</span>
            <span class="info-value">{data['risk_assessment']}</span>
        </div>
    </div>

    <div class="card">
        <h3>价格参考</h3>
        {f'<div class="info-row"><span class="info-label">建议入场价</span><span class="info-value">{data["entry_price"]:.2f}</span></div>' if data.get('entry_price') else ''}
        {f'<div class="info-row"><span class="info-label">止损价</span><span class="info-value">{data["stop_loss_price"]:.2f}</span></div>' if data.get('stop_loss_price') else ''}
        {f'<div class="info-row"><span class="info-label">目标价</span><span class="info-value">{data["target_price"]:.2f}</span></div>' if data.get('target_price') else ''}
        {f'<div class="info-row"><span class="info-label">预期收益</span><span class="info-value">{data["expected_return"]:.2f}%</span></div>' if data.get('expected_return') else ''}
        <div class="info-row">
            <span class="info-label">支撑位</span>
            <span class="info-value">{
                ', '.join([f'{x:.2f}' for x in data['support_levels']])
                if data['support_levels'] else '-'
            }</span>
        </div>
        <div class="info-row">
            <span class="info-label">压力位</span>
            <span class="info-value">{
                ', '.join([f'{x:.2f}' for x in data['resistance_levels']])
                if data['resistance_levels'] else '-'
            }</span>
        </div>
    </div>

    <div class="card">
        <h3>时机建议</h3>
        <p style="color: #666;">{data['timing_advice']}</p>
    </div>

    <div class="footer">
        <p>股票分析报告 v{data.get('generator_version', '1.0.0')}</p>
        <p>本报告仅供参考，不构成投资建议</p>
        <p>分析ID: {data['analysis_id']}</p>
    </div>
</body>
</html>
"""

    def _generate_json(self, data: dict[str, Any]) -> str:
        """生成 JSON 格式报告"""
        import json

        return json.dumps(data, ensure_ascii=False, indent=2)


# 全局报告生成器实例
_report_generator: ReportGenerator | None = None


def get_report_generator() -> ReportGenerator:
    """获取全局报告生成器实例"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
