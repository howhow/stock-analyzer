"""
分析器基类

定义分析器接口和通用方法
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from app.models.stock import DailyQuote, FinancialData, StockInfo
from app.utils.logger import get_logger

if TYPE_CHECKING:
    from app.models.analysis import AnalysisResult

logger = get_logger(__name__)


class AnalyzerResult:
    """
    分析器结果容器（内部使用）

    存储单次分析的结果，用于Analyst/Trader/SystemAnalyzer内部
    最终转换为models.analysis.AnalysisResult用于API响应
    """

    def __init__(self, analyzer_name: str):
        self.analyzer_name = analyzer_name
        self.scores: dict[str, float] = {}
        self.details: dict[str, Any] = {}
        self.signals: list[str] = []
        self.warnings: list[str] = []

    def add_score(self, dimension: str, score: float) -> None:
        """添加维度评分"""
        self.scores[dimension] = score

    def add_detail(self, key: str, value: Any) -> None:
        """添加详细信息"""
        self.details[key] = value

    def add_signal(self, signal: str) -> None:
        """添加信号"""
        self.signals.append(signal)

    def add_warning(self, warning: str) -> None:
        """添加警告"""
        self.warnings.append(warning)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "analyzer": self.analyzer_name,
            "scores": self.scores,
            "details": self.details,
            "signals": self.signals,
            "warnings": self.warnings,
        }

    def to_analysis_result(
        self,
        stock_code: str,
        stock_name: str | None = None,
        analysis_type: str = "both",
    ) -> "AnalysisResult":
        """
        转换为API响应模型（AnalysisResult）

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            analysis_type: 分析类型

        Returns:
            Pydantic AnalysisResult模型
        """
        import uuid
        from datetime import datetime

        from app.models.analysis import (
            AnalysisResult,
            AnalysisType,
            AnalystReport,
            DimensionScores,
            EntryTiming,
            MTFAlignment,
            Recommendation,
            TraderSignal,
        )

        # 提取评分
        scores = self.scores
        details = self.details

        # 构建分析师报告
        analyst_report = AnalystReport(
            stock_code=stock_code,
            stock_name=stock_name,
            analysis_type=AnalysisType(analysis_type),
            fundamental_score=scores.get("fundamental", 50.0) / 20.0,  # 转换为1-5
            technical_score=scores.get("technical", 50.0) / 20.0,
            dimension_scores=DimensionScores(
                signal_strength=scores.get("signal_strength", 3.0),
                opportunity_quality=scores.get("opportunity_quality", 3.0),
                risk_level=scores.get("risk_level", 3.0),
            ),
            total_score=scores.get("total", 50.0) / 20.0,
        )

        # 构建交易员信号
        trader_signal = TraderSignal(
            stock_code=stock_code,
            confidence=details.get("confidence", 50.0),
            mtf_alignment=MTFAlignment.NEUTRAL,  # 默认中性
            entry_timing=EntryTiming.WAIT,  # 默认等待
            recommendation=Recommendation(details.get("recommendation", "持有")),
        )

        # 构建最终结果
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            stock_code=stock_code,
            stock_name=stock_name,
            analysis_type=AnalysisType(analysis_type),
            analyst_report=analyst_report,
            trader_signal=trader_signal,
        )


class BaseAnalyzer(ABC):
    """
    分析器基类

    所有分析器必须继承此类
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"analyzer.{name}")

    @abstractmethod
    async def analyze(
        self,
        stock_info: StockInfo,
        quotes: list[DailyQuote],
        financial: FinancialData | None = None,
        **kwargs: Any,
    ) -> AnalyzerResult:
        """
        执行分析

        Args:
            stock_info: 股票基本信息
            quotes: 日线行情数据
            financial: 财务数据（可选）
            **kwargs: 其他参数

        Returns:
            分析器结果（内部容器）
        """
        pass

    def validate_data(
        self,
        quotes: list[DailyQuote],
        min_days: int = 20,
    ) -> bool:
        """
        验证数据是否足够分析

        Args:
            quotes: 日线数据
            min_days: 最少天数

        Returns:
            是否足够
        """
        return len(quotes) >= min_days

    def extract_price_series(
        self,
        quotes: list[DailyQuote],
    ) -> dict[str, list[float]]:
        """
        从日线数据提取价格序列

        Args:
            quotes: 日线数据

        Returns:
            {'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
        """
        # 按日期排序
        sorted_quotes = sorted(quotes, key=lambda x: x.trade_date)

        return {
            "open": [float(q.open) for q in sorted_quotes],
            "high": [float(q.high) for q in sorted_quotes],
            "low": [float(q.low) for q in sorted_quotes],
            "close": [float(q.close) for q in sorted_quotes],
            "volume": [float(q.volume) for q in sorted_quotes],
        }

    def calculate_basic_stats(
        self,
        quotes: list[DailyQuote],
    ) -> dict[str, float]:
        """
        计算基础统计信息

        Args:
            quotes: 日线数据

        Returns:
            统计信息字典
        """
        if not quotes:
            return {}

        sorted_quotes = sorted(quotes, key=lambda x: x.trade_date)
        closes = [q.close for q in sorted_quotes]

        # 价格变化
        price_change = (
            (closes[-1] - closes[0]) / closes[0] * 100 if len(closes) > 1 else 0
        )

        # 最高最低
        high_prices = [q.high for q in sorted_quotes]
        low_prices = [q.low for q in sorted_quotes]
        max_high = max(high_prices)
        min_low = min(low_prices)

        # 平均价格
        avg_price = sum(closes) / len(closes)

        # 当前价格位置
        current_position = (
            (closes[-1] - min_low) / (max_high - min_low) if max_high > min_low else 0.5
        )

        return {
            "price_change_pct": round(price_change, 2),
            "max_high": max_high,
            "min_low": min_low,
            "avg_price": round(avg_price, 2),
            "current_price": closes[-1],
            "current_position": round(current_position, 2),
            "days": len(quotes),
        }
