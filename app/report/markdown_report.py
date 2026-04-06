"""
Markdown 报告生成器

生成结构化的 Markdown 格式报告，供 AI agent 解析
"""

import json
from datetime import date
from typing import Any

from app.analysis.base import AnalysisResult
from app.models.stock import DailyQuote
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownReportGenerator:
    """Markdown 格式报告生成器"""
    
    def generate(
        self,
        result: AnalysisResult,
        stock_code: str | None = None,
        stock_name: str | None = None,
        quotes: list[DailyQuote] | None = None,
        indicators: dict[str, Any] | None = None,
    ) -> str:
        """
        生成 Markdown 格式报告
        
        Args:
            result: 分析结果
            stock_code: 股票代码（兼容简单 AnalysisResult）
            stock_name: 股票名称（兼容简单 AnalysisResult）
            quotes: 行情数据
            indicators: 技术指标
            
        Returns:
            Markdown 格式的报告文本
        """
        # 将额外信息添加到 result.details 中
        if stock_code:
            result.details["stock_code"] = stock_code
        if stock_name:
            result.details["stock_name"] = stock_name
        
        sections = [
            self._generate_header(result),
            self._generate_basic_info(result),
            self._generate_scores(result),
            self._generate_recommendation(result),
            self._generate_key_indicators(result, quotes, indicators),
            self._generate_technical_analysis(result, indicators),
            self._generate_fundamental_analysis(result),
            self._generate_risks(result),
            self._generate_opportunities(result),
            self._generate_trading_advice(result),
            self._generate_metadata(result),
        ]
        
        return "\n\n".join(sections)
    
    def _generate_header(self, result: AnalysisResult) -> str:
        """生成报告标题"""
        stock_name = result.details.get("stock_name", "未知")
        return f"# 股票分析报告 - {stock_name}"
    
    def _generate_basic_info(self, result: AnalysisResult) -> str:
        """生成基本信息"""
        stock_name = result.details.get("stock_name", "未知")
        analysis_type = result.details.get("analysis_type", "full")
        analysis_days = result.details.get("analysis_days", 120)
        
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
            f"| 股票代码 | {result.analyzer_name if hasattr(result, 'analyzer_name') else '-'} |",
            f"| 股票名称 | {stock_name} |",
            f"| 分析日期 | {date.today().strftime('%Y-%m-%d')} |",
            f"| 分析类型 | {type_map.get(analysis_type, analysis_type)} |",
            f"| 分析天数 | {analysis_days}天 |",
        ]
        
        return "\n".join(lines)
    
    def _generate_scores(self, result: AnalysisResult) -> str:
        """生成评分结果"""
        total_score = result.scores.get("total", 0)
        
        lines = [
            "## 评分结果",
            "",
            "| 维度 | 评分 |",
            "|-----|------|",
            f"| 综合评分 | {total_score:.1f}/100 |",
        ]
        
        # 获取分析师评分
        analyst_data = result.details.get("analyst", {})
        if analyst_data and "scores" in analyst_data:
            scores = analyst_data["scores"]
            if "fundamental" in scores:
                lines.append(f"| 基本面评分 | {scores['fundamental']:.1f} |")
            if "technical" in scores:
                lines.append(f"| 技术面评分 | {scores['technical']:.1f} |")
        
        # 获取交易员评分
        trader_data = result.details.get("trader", {})
        if trader_data and "scores" in trader_data:
            scores = trader_data["scores"]
            if "signal_strength" in scores:
                lines.append(f"| 信号强度 | {scores['signal_strength']:.1f}/5.0 |")
            if "opportunity_quality" in scores:
                lines.append(f"| 机会质量 | {scores['opportunity_quality']:.1f}/5.0 |")
            if "risk_level" in scores:
                lines.append(f"| 风险等级 | {scores['risk_level']:.1f}/5.0 |")
        
        return "\n".join(lines)
    
    def _generate_recommendation(self, result: AnalysisResult) -> str:
        """生成投资建议"""
        recommendation = result.details.get("recommendation", "无")
        confidence = result.details.get("confidence", 0)
        
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
            f"| 建议 | {rec_map.get(recommendation, recommendation)} |",
            f"| 置信度 | {confidence}% |",
        ]
        
        return "\n".join(lines)
    
    def _generate_key_indicators(
        self,
        result: AnalysisResult,
        quotes: list[DailyQuote] | None,
        indicators: dict[str, Any] | None,
    ) -> str:
        """生成关键指标"""
        lines = ["## 关键指标", ""]
        
        # 价格指标
        if quotes and len(quotes) > 0:
            latest = quotes[-1]
            high_30 = max(q.high for q in quotes[-30:]) if len(quotes) >= 30 else max(q.high for q in quotes)
            low_30 = min(q.low for q in quotes[-30:]) if len(quotes) >= 30 else min(q.low for q in quotes)
            
            lines.extend([
                "### 价格指标",
                "",
                "| 指标 | 数值 |",
                "|-----|------|",
                f"| 最新价 | {latest.close:.2f} |",
                f"| 30日最高 | {high_30:.2f} |",
                f"| 30日最低 | {low_30:.2f} |",
            ])
        
        return "\n".join(lines)
    
    def _generate_technical_analysis(
        self,
        result: AnalysisResult,
        indicators: dict[str, Any] | None,
    ) -> str:
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
        if result.signals:
            for signal in result.signals:
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
    
    def _generate_fundamental_analysis(self, result: AnalysisResult) -> str:
        """生成基本面分析"""
        lines = [
            "## 基本面分析",
            "",
            "### 财务状况",
            "",
            "| 项目 | 数值 |",
            "|-----|------|",
        ]
        
        # 从分析师结果获取基本面数据
        analyst_data = result.details.get("analyst", {})
        if analyst_data and "scores" in analyst_data:
            fund_score = analyst_data["scores"].get("fundamental", 0)
            lines.append(f"| 基本面评分 | {fund_score:.1f}/100 |")
        else:
            lines.append("| 数据 | 暂无 |")
        
        return "\n".join(lines)
    
    def _generate_risks(self, result: AnalysisResult) -> str:
        """生成风险提示"""
        lines = ["## 风险提示", ""]
        
        if result.warnings:
            for i, warning in enumerate(result.warnings, 1):
                lines.append(f"{i}. {warning}")
        else:
            lines.append("暂无明确风险提示")
        
        return "\n".join(lines)
    
    def _generate_opportunities(self, result: AnalysisResult) -> str:
        """生成投资机会"""
        lines = ["## 投资机会", ""]
        
        # 从信号中提取机会
        opportunities = []
        if result.signals:
            for signal in result.signals:
                if "上涨" in signal or "买入" in signal:
                    opportunities.append(signal)
        
        if opportunities:
            for i, opp in enumerate(opportunities, 1):
                lines.append(f"{i}. {opp}")
        else:
            lines.append("暂无明确投资机会")
        
        return "\n".join(lines)
    
    def _generate_trading_advice(self, result: AnalysisResult) -> str:
        """生成交易建议"""
        recommendation = result.details.get("recommendation", "无")
        confidence = result.details.get("confidence", 0)
        
        lines = [
            "## 交易建议",
            "",
            "| 项目 | 内容 |",
            "|-----|------|",
            f"| 操作方向 | {recommendation} |",
            f"| 置信度 | {confidence}% |",
        ]
        
        return "\n".join(lines)
    
    def _generate_metadata(self, result: AnalysisResult) -> str:
        """生成报告元数据"""
        stock_code = result.details.get("stock_code", "unknown")
        stock_name = result.details.get("stock_name", "未知")
        analysis_type = result.details.get("analysis_type", "full")
        analysis_days = result.details.get("analysis_days", 120)
        
        metadata = {
            "report_id": f"ana-{stock_code.replace('.', '-')}-{date.today().strftime('%Y%m%d')}",
            "stock_code": stock_code,
            "stock_name": stock_name,
            "analysis_date": date.today().strftime("%Y-%m-%d"),
            "analysis_type": analysis_type,
            "analysis_days": analysis_days,
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
