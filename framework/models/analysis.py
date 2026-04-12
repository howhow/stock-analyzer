"""
分析结果模型

定义分析结果的标准数据格式。
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """
    分析结果模型

    框架核心模块和插件返回的分析结果统一格式。
    """

    # 基本信息
    analysis_id: str = Field(..., description="分析ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str | None = Field(None, description="股票名称")
    analysis_type: Literal["short", "long", "both"] = Field(..., description="分析类型")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    # 评分结果
    total_score: float = Field(..., ge=0, le=100, description="综合评分")
    fundamental_score: float | None = Field(
        None, ge=0, le=100, description="基本面评分"
    )
    technical_score: float | None = Field(None, ge=0, le=100, description="技术面评分")
    sentiment_score: float | None = Field(None, ge=0, le=100, description="情绪面评分")

    # 信号
    signal: Literal["buy", "sell", "hold"] = Field(..., description="交易信号")
    signal_strength: float = Field(..., ge=0, le=5, description="信号强度（0-5）")
    confidence: float = Field(..., ge=0, le=100, description="置信度")

    # 详细信息
    details: dict[str, Any] = Field(default_factory=dict, description="详细信息")
    indicators: dict[str, Any] = Field(default_factory=dict, description="指标数据")
    recommendations: list[str] = Field(default_factory=list, description="建议列表")
    warnings: list[str] = Field(default_factory=list, description="风险警告")

    # 元数据
    data_source: str | None = Field(None, description="数据源")
    ai_provider: str | None = Field(None, description="AI提供商")
    processing_time_ms: float | None = Field(None, description="处理耗时")

    model_config = {"frozen": False, "extra": "ignore"}

    def get_risk_level(self) -> str:
        """获取风险等级"""
        if self.total_score >= 70:
            return "low"
        elif self.total_score >= 40:
            return "medium"
        else:
            return "high"

    def is_reliable(self) -> bool:
        """检查结果是否可靠（置信度足够高）"""
        return self.confidence >= 50

    def to_summary(self) -> str:
        """生成摘要文本"""
        signal_cn = {"buy": "买入", "sell": "卖出", "hold": "持有"}[self.signal]
        risk_cn = {
            "low": "低风险",
            "medium": "中风险",
            "high": "高风险",
        }[self.get_risk_level()]

        return (
            f"{self.stock_code} | 综合评分: {self.total_score:.1f} | "
            f"信号: {signal_cn} | 风险: {risk_cn}"
        )
