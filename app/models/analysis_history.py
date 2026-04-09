"""
分析历史模型

存储用户分析历史记录
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AnalysisHistory(Base):
    """分析历史模型"""

    __tablename__ = "analysis_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """主键ID"""

    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    """用户ID"""

    # 分析目标
    stock_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    """股票代码"""

    stock_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    """股票名称"""

    analysis_type: Mapped[str] = mapped_column(String(16), nullable=False)
    """分析类型（fundamental/technical/both）"""

    # 分析结果
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    """总评分（1-5）"""

    fundamental_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    """基本面评分（1-5）"""

    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    """技术面评分（1-5）"""

    recommendation: Mapped[str] = mapped_column(String(16), nullable=False)
    """投资建议（强烈买入/买入/持有/减持/卖出）"""

    # 详细数据
    analysis_result: Mapped[str] = mapped_column(Text, nullable=False)
    """完整分析结果（JSON）"""

    # 元数据
    analysis_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    """分析耗时（毫秒）"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    """创建时间"""

    def __repr__(self) -> str:
        return f"<AnalysisHistory(id={self.id}, stock_code={self.stock_code})>"
