"""
Markdown 报告生成器

生成结构化的 Markdown 格式报告，供 AI agent 解析
"""

import json
from datetime import date
from typing import Any

from app.report.report_data import ReportData
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownReportGenerator:
    """Markdown 格式报告生成器"""

    def generate(self, data: ReportData) -> str:
        """
        生成 Markdown 格式报告

        Args:
            data: 报告数据容器

        Returns:
            Markdown 格式的报告文本
        """
        # 将额外信息添加到 result.details 中
        data.result.details["stock_code"] = data.stock_code
        data.result.details["stock_name"] = data.stock_name

        sections = [
            self._generate_header(data),
            self._generate_basic_info(data),
            self._generate_scores(data),
            self._generate_recommendation(data),
            self._generate_key_indicators(data),
            self._generate_technical_analysis(data),
            self._generate_fundamental_analysis(data),
            self._generate_risks(data),
            self._generate_opportunities(data),
            self._generate_trading_advice(data),
            self._generate_metadata(data),
        ]

        return "\n\n".join(sections)

    def _generate_header(self, data: ReportData) -> str:
        """生成报告标题"""
        return f"# 股票分析报告 - {data.stock_name}"

    def _generate_basic_info(self, data: ReportData) -> str:
        """生成基本信息"""
        analysis_type = data.result.details.get("analysis_type", "full")
        
        type_map = {
            "full": "完整分析",
            "technical": "技术分析",
            "fundamental": "基本面分析",
        }

        lines = [
            "## 基本信息",
            "",
            "| 项目 | 内容 |",
            "|-----|------|",
            f"| 股票代码 | {data.stock_code} |",
            f"| 股票名称 | {data.stock_name} |",
            f"| 分析日期 | {data.report_date.strftime('%Y-%m-%d')} |",
            f"| 分析类型 | {type_map.get(analysis_type, analysis_type)} |",
            f"| 分析天数 | {data.analysis_days} 天 |",
        ]

        return "\n".join(lines)

    def _generate_scores(self, data: ReportData) -> str:
        """生成评分结果"""
        lines = [
            "## 评分结果",
            "",
            "| 维度 | 评分 |",
            "|-----|------|",
            f"| 综合评分 | {data.total_score:.1f}/100 |",
        ]

        # 获取分析师评分
        analyst_data = data.result.details.get("analyst", {})
        if analyst_data and "scores" in analyst_data:
            scores = analyst_data["scores"]
            if "fundamental" in scores:
                lines.append(f"| 基本面评分 | {scores['fundamental']:.1f} |")
            if "technical" in scores:
                lines.append(f"| 技术面评分 | {scores['technical']:.1f} |")

        # 获取交易员评分
        trader_data = data.result.details.get("trader", {})
        if trader_data and "scores" in trader_data:
            scores = trader_data["scores"]
            if "signal_strength" in scores:
                lines.append(f"| 信号强度 | {scores['signal_strength']:.1f}/5.0 |")
            if "opportunity_quality" in scores:
                lines.append(f"| 机会质量 | {scores['opportunity_quality']:.1f}/5.0 |")
            if "risk_level" in scores:
                lines.append(f"| 风险等级 | {scores['risk_level']:.1f}/5.0 |")

        return "\n".join(lines)

    def _generate_recommendation(self, data: ReportData) -> str:
        """生成投资建议"""
        rec_map = {
            "强烈买入": "强烈买入",
            "买入": "买入",
            "持有": "持有",
            "减持": "减持",
            "卖出": "卖出",
            "强烈卖出": "强烈卖出",
        }

        lines = [
            "## 投资建议",
            "",
            "| 项目 | 内容 |",
            "|-----|------|",
            f"| 建议 | {rec_map.get(data.recommendation, data.recommendation)} |",
            f"| 置信度 | {data.confidence}% |",
        ]

        return "\n".join(lines)

    def _generate_key_indicators(self, data: ReportData) -> str:
        """生成关键指标"""
        lines = ["## 关键指标", ""]

        # 价格指标
        if data.quotes and len(data.quotes) > 0:
            latest = data.quotes[-1]
            high_30 = (
                max(q.high for q in data.quotes[-30:])
                if len(data.quotes) >= 30
                else max(q.high for q in data.quotes)
            )
            low_30 = (
                min(q.low for q in data.quotes[-30:])
                if len(data.quotes) >= 30
                else min(q.low for q in data.quotes)
            )

            lines.extend(
                [
                    "### 价格指标",
                    "",
                    "| 指标 | 数值 |",
                    "|-----|------|",
                    f"| 最新价 | {latest.close:.2f} |",
                    f"| 30日最高 | {high_30:.2f} |",
                    f"| 30日最低 | {low_30:.2f} |",
                ]
            )

        return "\n".join(lines)

    def _generate_technical_analysis(self, data: ReportData) -> str:
        """生成技术分析"""
        lines = [
            "## 技术分析",
            "",
            "### 趋势判断",
            "",
            "| 周期 | 趋势 | 强度 |",
            "|-----|------|------|",
        ]

        # 从信号中提取趋势信息
        if data.signals:
            for signal in data.signals:
                if "上涨趋势" in signal:
                    lines.append("| 中期 | 上涨 | 中 |")
                    break
                elif "下跌趋势" in signal:
                    lines.append("| 中期 | 下跌 | 中 |")
                    break
            else:
                lines.append("| 中期 | 震荡 | 弱 |")
        else:
            lines.append("| 中期 | - | - |")

        return "\n".join(lines)

    def _generate_fundamental_analysis(self, data: ReportData) -> str:
        """生成基本面分析"""
        lines = [
            "## 基本面分析",
            "",
        ]

        # DCF 估值结果
        dcf_data = data.result.details.get("dcf")
        if dcf_data:
            lines.extend([
                "### DCF 估值",
                "",
                "| 指标 | 数值 |",
                "|-----|------|",
                f"| DCF估值 | ¥{dcf_data.get('dcf_mean', 0):.2f} |",
                f"| 估值状态 | {dcf_data.get('valuation', '未知')} |",
            ])
            lines.append("")

        # 安全边际
        safety_data = data.result.details.get("safety_margin")
        if safety_data:
            lines.extend([
                "### 安全边际",
                "",
                "| 指标 | 数值 |",
                "|-----|------|",
                f"| 当前价格 | ¥{safety_data.get('current_price', 0):.2f} |",
                f"| DCF价值 | ¥{safety_data.get('dcf_value', 0):.2f} |",
                f"| 安全边际 | {safety_data.get('margin_percent', 0):.1f}% |",
                f"| 评级 | {safety_data.get('rating', '未知')} |",
            ])
            lines.append("")

        # 四季引擎
        seasons_data = data.result.details.get("seasons")
        if seasons_data:
            lines.extend([
                "### 四季分析",
                "",
                "| 指标 | 数值 |",
                "|-----|------|",
                f"| 当前季节 | {seasons_data.get('current_season', '未知')} |",
                f"| 置信度 | {seasons_data.get('confidence', 0):.2f} |",
            ])
            lines.append("")

        # 五行引擎
        wuxing_data = data.result.details.get("wuxing")
        if wuxing_data:
            lines.extend([
                "### 五行分析",
                "",
                "| 指标 | 数值 |",
                "|-----|------|",
                f"| 五行属性 | {wuxing_data.get('element', '未知')} |",
                f"| 置信度 | {wuxing_data.get('confidence', 0):.2f} |",
                f"| 建议操作 | {wuxing_data.get('action', '未知') or '观望'} |",
            ])
            lines.append("")

        # 基础财务数据
        if data.fundamentals:
            lines.extend([
                "### 财务指标",
                "",
                "| 指标 | 数值 |",
                "|-----|------|",
            ])
            for key, value in data.fundamentals.items():
                if value is not None and key not in ['report_date']:
                    if isinstance(value, (int, float)):
                        lines.append(f"| {key} | {value:.2f} |")
                    else:
                        lines.append(f"| {key} | {value} |")
            lines.append("")
        else:
            # 从分析师结果获取基本面数据
            analyst_data = data.result.details.get("analyst", {})
            if analyst_data and "scores" in analyst_data:
                fund_score = analyst_data["scores"].get("fundamental", 0)
                lines.extend([
                    "### 基本面评分",
                    "",
                    f"| 项目 | 数值 |",
                    f"|-----|------|",
                    f"| 基本面评分 | {fund_score:.1f}/100 |",
                ])
            else:
                lines.append("暂无详细基本面数据")

        return "\n".join(lines)

    def _generate_risks(self, data: ReportData) -> str:
        """生成风险提示"""
        lines = ["## 风险提示", ""]

        if data.warnings:
            for i, warning in enumerate(data.warnings, 1):
                lines.append(f"{i}. {warning}")
        else:
            lines.append("暂无明确风险提示")

        return "\n".join(lines)

    def _generate_opportunities(self, data: ReportData) -> str:
        """生成投资机会"""
        lines = ["## 投资机会", ""]

        # 从信号中提取机会
        opportunities = []
        if data.signals:
            for signal in data.signals:
                if "上涨" in signal or "买入" in signal:
                    opportunities.append(signal)

        if opportunities:
            for i, opp in enumerate(opportunities, 1):
                lines.append(f"{i}. {opp}")
        else:
            lines.append("暂无明确投资机会")

        return "\n".join(lines)

    def _generate_trading_advice(self, data: ReportData) -> str:
        """生成交易建议"""
        lines = [
            "## 交易建议",
            "",
            "| 项目 | 内容 |",
            "|-----|------|",
            f"| 操作方向 | {data.recommendation} |",
            f"| 置信度 | {data.confidence}% |",
        ]

        return "\n".join(lines)

    def _generate_metadata(self, data: ReportData) -> str:
        """生成报告元数据"""
        report_id = (
            f"ana-{data.stock_code.replace('.', '-')}-{date.today().strftime('%Y%m%d')}"
        )
        metadata = {
            "report_id": report_id,
            "stock_code": data.stock_code,
            "stock_name": data.stock_name,
            "analysis_date": data.report_date.strftime("%Y-%m-%d"),
            "analysis_type": data.analysis_type,
            "analysis_days": data.analysis_days,
            "generated_at": date.today().isoformat(),
            "version": "1.0.0",
        }

        lines = [
            "---",
            "",
            "**报告元数据**",
            "",
            "```json",
            json.dumps(metadata, ensure_ascii=False, indent=2),
            "```",
        ]

        return "\n".join(lines)
