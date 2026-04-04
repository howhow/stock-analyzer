"""
分析结果模型

定义分析相关的数据结构
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AnalysisType(str, Enum):
    """分析类型"""

    LONG = "long"  # 长线分析
    SHORT = "short"  # 短线分析
    BOTH = "both"  # 综合分析


class ReportType(str, Enum):
    """报告类型"""

    SIMPLE = "simple"  # 简洁版
    DETAILED = "detailed"  # 详细版


class AnalysisMode(str, Enum):
    """分析模式"""

    ALGORITHM = "algorithm"  # 纯算法（默认）
    AI_ENHANCED = "ai_enhanced"  # AI增强


class WyckoffPhase(str, Enum):
    """威科夫阶段"""

    ACCUMULATION = "accumulation"  # 吸筹
    MARKUP = "markup"  # 上涨
    DISTRIBUTION = "distribution"  # 派发
    MARKDOWN = "markdown"  # 下跌
    UNKNOWN = "unknown"  # 未知


class MTFAlignment(str, Enum):
    """多时间框架对齐状态"""

    ALIGNED = "aligned"  # 一致
    CONFLICT = "conflict"  # 冲突
    NEUTRAL = "neutral"  # 中性


class EntryTiming(str, Enum):
    """入场时机"""

    IMMEDIATE = "immediate"  # 立即入场
    WAIT = "wait"  # 等待
    AVOID = "avoid"  # 避免


class Recommendation(str, Enum):
    """投资建议"""

    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"


# ============ 评分模型 ============


class DimensionScores(BaseModel):
    """三维度评分"""

    signal_strength: float = Field(..., ge=1, le=5, description="信号强度 (1-5)")
    opportunity_quality: float = Field(..., ge=1, le=5, description="机会质量 (1-5)")
    risk_level: float = Field(
        ..., ge=1, le=5, description="风险等级 (1-5, 5为最低风险)"
    )

    def validate_scores(self) -> None:
        """验证评分范围"""
        for name, value in [
            ("signal_strength", self.signal_strength),
            ("opportunity_quality", self.opportunity_quality),
            ("risk_level", self.risk_level),
        ]:
            if not 1 <= value <= 5:
                raise ValueError(f"{name} must be in [1, 5], got {value}")


class AnalystReport(BaseModel):
    """分析师报告"""

    stock_code: str = Field(..., description="股票代码")
    stock_name: str | None = Field(default=None, description="股票名称")
    analysis_type: AnalysisType = Field(..., description="分析类型")

    # 评分
    fundamental_score: float = Field(..., ge=1, le=5, description="基本面评分")
    technical_score: float = Field(..., ge=1, le=5, description="技术面评分")
    dimension_scores: DimensionScores = Field(..., description="三维度评分")
    total_score: float = Field(..., ge=1, le=5, description="综合评分")

    # 技术分析
    wyckoff_phase: WyckoffPhase = Field(
        default=WyckoffPhase.UNKNOWN, description="威科夫阶段"
    )
    support_levels: list[float] = Field(default_factory=list, description="支撑位")
    resistance_levels: list[float] = Field(default_factory=list, description="压力位")

    # 元数据
    analysis_time: datetime = Field(
        default_factory=datetime.now, description="分析时间"
    )
    data_updated_at: datetime | None = Field(default=None, description="数据更新时间")

    model_config = {"frozen": False}


class TraderSignal(BaseModel):
    """交易员信号"""

    stock_code: str = Field(..., description="股票代码")
    confidence: float = Field(..., ge=0, le=100, description="置信度 (0-100)")
    mtf_alignment: MTFAlignment = Field(..., description="多时间框架对齐")
    entry_timing: EntryTiming = Field(..., description="入场时机")
    recommendation: Recommendation = Field(..., description="投资建议")

    # 风险指标
    expected_return: float | None = Field(default=None, description="预期收益率(%)")
    var_95: float | None = Field(default=None, description="VaR 95%(%)")
    max_drawdown: float | None = Field(default=None, description="最大回撤(%)")

    # 时机建议
    entry_price: float | None = Field(default=None, description="建议入场价")
    stop_loss_price: float | None = Field(default=None, description="止损价")
    target_price: float | None = Field(default=None, description="目标价")

    # 元数据
    signal_time: datetime = Field(default_factory=datetime.now, description="信号时间")

    model_config = {"frozen": False}


class AnalysisResult(BaseModel):
    """完整分析结果"""

    analysis_id: str = Field(..., description="分析ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str | None = Field(default=None, description="股票名称")
    analysis_type: AnalysisType = Field(..., description="分析类型")
    mode: AnalysisMode = Field(default=AnalysisMode.ALGORITHM, description="分析模式")

    # 报告
    analyst_report: AnalystReport = Field(..., description="分析师报告")
    trader_signal: TraderSignal = Field(..., description="交易员信号")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    processing_time_ms: float | None = Field(default=None, description="处理耗时(ms)")

    model_config = {"frozen": False}


# ============ 请求模型 ============


class AnalysisRequest(BaseModel):
    """分析请求"""

    stock_code: str = Field(..., description="股票代码")
    analysis_type: AnalysisType = Field(
        default=AnalysisType.BOTH, description="分析类型"
    )
    mode: AnalysisMode = Field(default=AnalysisMode.ALGORITHM, description="分析模式")
    report_type: ReportType = Field(default=ReportType.SIMPLE, description="报告类型")

    @field_validator("stock_code")
    @classmethod
    def validate_stock_code(cls, v: str) -> str:
        """验证股票代码"""
        if not v:
            raise ValueError("stock_code cannot be empty")
        return v.upper()


class BatchAnalysisRequest(BaseModel):
    """批量分析请求"""

    stock_codes: list[str] = Field(
        ..., min_length=1, max_length=50, description="股票代码列表"
    )
    analysis_type: AnalysisType = Field(
        default=AnalysisType.BOTH, description="分析类型"
    )
    mode: AnalysisMode = Field(default=AnalysisMode.ALGORITHM, description="分析模式")


# ============ 响应模型 ============


class AnalysisResponse(BaseModel):
    """分析响应（简洁版）"""

    analysis_id: str = Field(..., description="分析ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str | None = Field(default=None, description="股票名称")
    scores: DimensionScores = Field(..., description="评分")
    total_score: float = Field(..., description="综合评分")
    recommendation: Recommendation = Field(..., description="投资建议")
    confidence: float = Field(..., description="置信度")

    model_config = {"frozen": False}
