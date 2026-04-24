"""
报告数据模型 — 统一的数据容器

设计原则:
- 单一数据源：所有报告格式（HTML/Markdown/PDF）共享同一份数据
- 格式无关：数据组装与格式渲染分离
- 类型安全：使用 dataclass 确保数据完整性
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.analysis.base import AnalyzerResult
from app.models.stock import DailyQuote


@dataclass
class ReportData:
    """报告数据容器 — 所有报告格式的统一数据源

    使用方式:
        data = ReportData.from_analysis(
            result=analyzer_result,
            stock_code="000001.SZ",
            stock_name="平安银行",
            quotes=daily_quotes,
            indicators=technical_indicators,
            fundamentals=fundamental_data,
        )

        # HTML 格式
        html = HTMLReportGenerator().generate(data)

        # Markdown 格式
        md = MarkdownReportGenerator().generate(data)
    """

    # 股票基本信息
    stock_code: str
    stock_name: str

    # 分析结果（核心数据）
    result: AnalyzerResult

    # 行情数据（可选）
    quotes: list[DailyQuote] = field(default_factory=list)

    # 技术指标（可选）
    indicators: dict[str, Any] = field(default_factory=dict)

    # 基本面数据（可选）
    fundamentals: dict[str, Any] = field(default_factory=dict)

    # 报告元数据
    report_date: date = field(default_factory=date.today)
    analysis_days: int = 120
    analysis_type: str = "full"

    @classmethod
    def from_analysis(
        cls,
        result: AnalyzerResult,
        stock_code: str,
        stock_name: str,
        quotes: list[DailyQuote] | None = None,
        indicators: dict[str, Any] | None = None,
        fundamentals: dict[str, Any] | None = None,
        analysis_days: int = 120,
        analysis_type: str = "full",
    ) -> "ReportData":
        """从分析结果创建报告数据

        Args:
            result: 分析结果
            stock_code: 股票代码
            stock_name: 股票名称
            quotes: 行情数据（可选）
            indicators: 技术指标（可选）
            fundamentals: 基本面数据（可选）
            analysis_days: 分析天数
            analysis_type: 分析类型

        Returns:
            ReportData 实例
        """
        return cls(
            stock_code=stock_code,
            stock_name=stock_name,
            result=result,
            quotes=quotes or [],
            indicators=indicators or {},
            fundamentals=fundamentals or {},
            analysis_days=analysis_days,
            analysis_type=analysis_type,
        )

    @property
    def total_score(self) -> float:
        """综合评分"""
        return self.result.scores.get("total", 0)

    @property
    def recommendation(self) -> str:
        """投资建议"""
        result: str = self.result.details.get("recommendation", "无")
        return result

    @property
    def confidence(self) -> int:
        """置信度"""
        result: int = self.result.details.get("confidence", 0)
        return result

    @property
    def latest_price(self) -> float | None:
        """最新价格"""
        if self.quotes:
            return self.quotes[-1].close
        return None

    @property
    def signals(self) -> list[str]:
        """交易信号列表"""
        return self.result.signals or []

    @property
    def warnings(self) -> list[str]:
        """风险提示列表"""
        return self.result.warnings or []
