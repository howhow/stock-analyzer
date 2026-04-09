"""
用户配置模型

存储用户AI配置和分析偏好
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserConfig(Base):
    """用户配置模型"""

    __tablename__ = "user_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """主键ID"""

    user_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    """用户ID（唯一）"""

    # AI配置
    openai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    """OpenAI API Key（加密存储）"""

    openai_base_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    """OpenAI API Base URL"""

    openai_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    """OpenAI 模型名称"""

    anthropic_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Anthropic API Key（加密存储）"""

    anthropic_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    """Anthropic 模型名称"""

    # 分析偏好
    default_analysis_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="both"
    )
    """默认分析类型（fundamental/technical/both）"""

    default_days: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    """默认分析天数"""

    # 飞书推送配置（v1.2预留）
    feishu_webhook_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    """飞书Webhook URL"""

    feishu_push_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    """是否启用飞书推送"""

    # 元数据
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    """创建时间"""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    """更新时间"""

    def __repr__(self) -> str:
        return f"<UserConfig(id={self.id}, user_id={self.user_id})>"
