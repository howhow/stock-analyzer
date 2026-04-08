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
from app.models.report import ReportContent, ReportFormat
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
        stock_code: str | None = None,
        stock_name: str | None = None,
        format_type: ReportFormat = ReportFormat.HTML,
        chart_data: dict[str, Any] | None = None,
        indicators: dict[str, Any] | None = None,
        fundamentals: dict[str, Any] | None = None,
    ) -> ReportContent:
        """
        生成分析报告

        Args:
            analysis_result: 分析结果
            stock_code: 股票代码（兼容简单 AnalysisResult）
            stock_name: 股票名称（兼容简单 AnalysisResult）
            format_type: 报告格式
            chart_data: 图表数据（K线、MA、成交量、MACD、RSI等）
            indicators: 技术指标数据
            fundamentals: 基本面数据

        Returns:
            报告内容
        """
        report_id = self._generate_report_id()

        # 兼容简单 AnalysisResult（app/analysis/base.py）
        # 如果传入的是简单 AnalysisResult，需要从参数获取 stock_code
        actual_stock_code = stock_code or getattr(
            analysis_result, "stock_code", "UNKNOWN"
        )
        actual_stock_name = stock_name or getattr(analysis_result, "stock_name", "未知")

        logger.info(
            "report_generation_started",
            report_id=report_id,
            stock_code=actual_stock_code,
            format=format_type.value,
        )

        try:
            # 准备报告数据
            report_data = self._prepare_report_data(
                analysis_result, chart_data, indicators, fundamentals
            )

            # 生成报告内容
            if format_type == ReportFormat.HTML:
                content = self._generate_html(report_data)
            elif format_type == ReportFormat.JSON:
                content = self._generate_json(report_data)
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            report_content = ReportContent(
                report_id=report_id,
                stock_code=str(actual_stock_code),
                stock_name=str(actual_stock_name),
                analysis_data=report_data,
                generator_version=self.version,
                content=content,
            )

            logger.info(
                "report_generation_completed",
                report_id=report_id,
                stock_code=actual_stock_code,
                content_length=len(content),
            )

            return report_content

        except Exception as e:
            logger.error(
                "report_generation_failed",
                report_id=report_id,
                stock_code=actual_stock_code,
                error=str(e),
            )
            raise

    def _generate_report_id(self) -> str:
        """生成报告ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"rpt_{timestamp}_{unique_id}"

    def _prepare_report_data(
        self,
        result: AnalysisResult,
        chart_data: dict[str, Any] | None = None,
        indicators: dict[str, Any] | None = None,
        fundamentals: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        准备报告数据

        Args:
            result: 分析结果（支持简单 AnalysisResult）
            chart_data: 图表数据
            indicators: 技术指标数据
            fundamentals: 基本面数据

        Returns:
            报告数据字典
        """
        # 兼容两种 AnalysisResult 格式
        # 1. 简单版本（app/analysis/base.py）- 有 details 属性
        # 2. 完整版本（app/models/analysis.py）- 有 analyst_report 和 trader_signal 属性

        if hasattr(result, "details"):
            # 简单版本
            analyst_data = result.details.get("analyst", {})
            trader_data = result.details.get("trader", {})
            scores = {
                "total": result.details.get("total_score", 0),
                "fundamental": analyst_data.get("scores", {}).get("fundamental", 50),
                "technical": analyst_data.get("scores", {}).get("technical", 50),
                "signal_strength": trader_data.get("scores", {}).get(
                    "signal_strength", 2.5
                ),
                "opportunity_quality": trader_data.get("scores", {}).get(
                    "opportunity_quality", 2.5
                ),
                "risk_level": trader_data.get("scores", {}).get("risk_level", 3),
            }
            risk_assessment = self._calculate_risk_assessment(
                scores["risk_level"],
                trader_data.get("var_95", 0),
                trader_data.get("max_drawdown", 0),
            )
            stock_code = result.details.get("stock_code", "UNKNOWN")
            stock_name = result.details.get("stock_name", "未知")
            analysis_type = result.details.get("analysis_type", "long")
            recommendation = result.details.get("recommendation", "hold")
            confidence = result.details.get("confidence", 50)
        else:
            # 完整版本（app/models/analysis.py）
            analyst_report = result.analyst_report
            trader_signal = result.trader_signal

            scores = {
                "total": analyst_report.total_score,
                "fundamental": analyst_report.fundamental_score,
                "technical": analyst_report.technical_score,
                "signal_strength": (analyst_report.dimension_scores.signal_strength),
                "opportunity_quality": (
                    analyst_report.dimension_scores.opportunity_quality
                ),
                "risk_level": analyst_report.dimension_scores.risk_level,
            }
            risk_assessment = self._calculate_risk_assessment(
                scores["risk_level"],
                trader_signal.var_95,
                trader_signal.max_drawdown,
            )
            stock_code = result.stock_code
            stock_name = result.stock_name or "未知"
            analysis_type = (
                result.analysis_type.value
                if hasattr(result.analysis_type, "value")
                else str(result.analysis_type)
            )
            recommendation = (
                trader_signal.recommendation.value
                if hasattr(trader_signal.recommendation, "value")
                else str(trader_signal.recommendation)
            )
            confidence = trader_signal.confidence

            # 为后续代码准备 trader_data 字典
            trader_data = {
                "entry_timing": (
                    trader_signal.entry_timing.value
                    if hasattr(trader_signal.entry_timing, "value")
                    else str(trader_signal.entry_timing)
                ),
                "entry_price": trader_signal.entry_price,
                "stop_loss_price": trader_signal.stop_loss_price,
                "var_95": trader_signal.var_95,
                "max_drawdown": trader_signal.max_drawdown,
            }
            analyst_data = analyst_data if "analyst_data" in locals() else {}

        # 时机建议
        timing_advice = self._generate_timing_advice(
            trader_data.get("entry_timing", "观望"),
            trader_data.get("entry_price", 0),
            trader_data.get("stop_loss_price", 0),
        )

        # 动态风险提示
        risk_warnings = self._generate_risk_warnings(
            indicators=indicators,
            var_95=trader_data.get("var_95", 0),
            max_drawdown=trader_data.get("max_drawdown", 0),
        )

        # 图表数据（使用传入数据或生成模拟数据）
        final_chart_data = chart_data or self._generate_mock_chart_data(result)

        # 指标数据
        final_indicators = indicators or {}

        # 基本面数据
        final_fundamentals = fundamentals or {}

        # 波动率（从指标或计算）
        volatility_30d = final_indicators.get("volatility_30d", None)

        return {
            # 基本信息
            "stock_code": stock_code,
            "stock_name": stock_name,
            "analysis_id": f"analysis_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "analysis_type": analysis_type,
            "mode": "algorithm",
            "generated_at": datetime.now().isoformat(),
            # 评分
            "scores": scores,
            "score_grade": self._get_score_grade(scores["total"]),
            # 分析结论
            "recommendation": recommendation,
            "confidence": confidence,
            "wyckoff_phase": analyst_data.get("wyckoff_phase", "accumulation"),
            "mtf_alignment": trader_data.get("mtf_alignment", "neutral"),
            "entry_timing": trader_data.get("entry_timing", "观望"),
            # 价格信息
            "support_levels": analyst_data.get("support_levels", []),
            "resistance_levels": analyst_data.get("resistance_levels", []),
            "entry_price": trader_data.get("entry_price", 0),
            "stop_loss_price": trader_data.get("stop_loss_price", 0),
            "target_price": trader_data.get("target_price", 0),
            "expected_return": trader_data.get("expected_return", 0),
            # 风险评估
            "risk_assessment": risk_assessment,
            "var_95": trader_data.get("var_95", 0),
            "max_drawdown": trader_data.get("max_drawdown", 0),
            "volatility_30d": volatility_30d,
            # 时机建议
            "timing_advice": timing_advice,
            # 新增：图表数据
            "chart_data": final_chart_data,
            # 新增：技术指标
            "indicators": final_indicators,
            # 新增：基本面数据
            "fundamentals": final_fundamentals,
            # 新增：动态风险提示
            "risk_warnings": risk_warnings,
            # 生成器版本
            "generator_version": self.version,
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

    def _generate_risk_warnings(
        self,
        indicators: dict[str, Any] | None = None,
        var_95: float | None = None,
        max_drawdown: float | None = None,
    ) -> list[str]:
        """
        生成动态风险提示

        根据PRD v1.03 4.6.5 规则生成

        Args:
            indicators: 技术指标数据
            var_95: VaR(95%)
            max_drawdown: 最大回撤

        Returns:
            风险提示列表
        """
        warnings = []
        indicators = indicators or {}

        # 规则1: 换手率 > 10%
        turnover_rate = indicators.get("turnover_rate", 0)
        if turnover_rate > 10:
            warnings.append(f"近期换手率偏高（{turnover_rate:.1f}%），注意流动性风险")

        # 规则2: 30日波动率 > 3%
        volatility_30d = indicators.get("volatility_30d", 0)
        if volatility_30d > 3:
            warnings.append(f"30日波动率较高（{volatility_30d:.1f}%），价格波动剧烈")

        # 规则3: 成交量比 > 2
        volume_ratio = indicators.get("volume_ratio", 0)
        if volume_ratio > 2:
            warnings.append(f"成交量异常放大（{volume_ratio:.1f}倍），可能存在资金异动")

        # 额外规则: VaR风险提示
        if var_95 is not None and var_95 > 5:
            warnings.append(f"VaR(95%)较高（{var_95:.1f}%），潜在损失风险较大")

        # 额外规则: 最大回撤风险提示
        if max_drawdown is not None and max_drawdown > 15:
            warnings.append(f"历史最大回撤较大（{max_drawdown:.1f}%），注意下行风险")

        # 如果没有触发任何规则，返回默认提示
        if not warnings:
            warnings.append("当前未检测到明显风险信号，但仍需关注市场变化")

        return warnings

    def _generate_mock_chart_data(self, result: AnalysisResult) -> dict[str, Any]:
        """
        生成模拟图表数据（用于测试）

        实际使用时应从外部传入真实的图表数据

        Args:
            result: 分析结果

        Returns:
            图表数据字典
        """
        import random

        # 生成60个交易日的模拟数据
        days = 60
        dates = []
        kline = []
        volume = []
        ma5 = []
        ma20 = []

        # 基于支撑压力位设定基础价格
        base_price = 46.0

        # 兼容两种 AnalysisResult 格式
        if hasattr(result, "details"):
            # 简单版本
            analyst_data = result.details.get("analyst", {})
            support_levels = analyst_data.get("support_levels", [44.0])
            resistance_levels = analyst_data.get("resistance_levels", [50.0])
        else:
            # 完整版本
            support_levels = result.analyst_report.support_levels or [44.0]
            resistance_levels = result.analyst_report.resistance_levels or [50.0]

        support = support_levels[0] if support_levels else 44.0
        resistance = resistance_levels[0] if resistance_levels else 50.0

        # 生成日期
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)
        for i in range(days):
            date = start_date + timedelta(days=i)
            if date.weekday() < 5:  # 只生成工作日
                dates.append(date.strftime("%m-%d"))

        # 生成K线数据
        close = base_price
        for i in range(len(dates)):
            # 随机波动
            change = random.uniform(-0.03, 0.03)
            open_price = close
            close = close * (1 + change)
            high = max(open_price, close) * (1 + random.uniform(0, 0.01))
            low = min(open_price, close) * (1 - random.uniform(0, 0.01))

            kline.append(
                [
                    round(open_price, 2),
                    round(close, 2),
                    round(low, 2),
                    round(high, 2),
                ]
            )

            # 成交量（单位：万手）
            volume.append(random.randint(500, 2000))

        # 计算MA5和MA20
        for i in range(len(kline)):
            if i >= 4:
                ma5_val = sum([kline[j][1] for j in range(i - 4, i + 1)]) / 5
                ma5.append(round(ma5_val, 2))
            else:
                ma5.append(0.0)  # type: ignore[arg-type]

            if i >= 19:
                ma20_val = sum([kline[j][1] for j in range(i - 19, i + 1)]) / 20
                ma20.append(round(ma20_val, 2))
            else:
                ma20.append(0.0)  # type: ignore[arg-type]

        # 生成MACD数据
        macd_dif = []
        macd_dea = []
        macd_histogram = []

        for i in range(len(kline)):
            if i >= 20:
                dif = random.uniform(-0.5, 0.5)
                dea = random.uniform(-0.3, 0.3)
                hist = (dif - dea) * 2
                macd_dif.append(round(dif, 3))
                macd_dea.append(round(dea, 3))
                macd_histogram.append(round(hist, 3))
            else:
                macd_dif.append(None)
                macd_dea.append(None)
                macd_histogram.append(None)

        # 生成RSI数据
        rsi_data = []
        for i in range(len(kline)):
            if i >= 14:
                rsi_val = random.uniform(30, 70)
                rsi_data.append(round(rsi_val, 1))
            else:
                rsi_data.append(None)

        return {
            "dates": dates,
            "kline": kline,
            "volume": volume,
            "ma5": ma5,
            "ma20": ma20,
            "support": round(support, 2),
            "resistance": round(resistance, 2),
            "macd": {
                "dif": macd_dif,
                "dea": macd_dea,
                "histogram": macd_histogram,
            },
            "rsi": rsi_data,
        }

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
