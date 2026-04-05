"""
报告模型

定义报告相关的数据结构
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ReportStatus(str, Enum):
    """报告状态"""

    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 生成失败
    EXPIRED = "expired"  # 已过期


class ReportFormat(str, Enum):
    """报告格式"""

    HTML = "html"  # HTML格式
    PDF = "pdf"  # PDF格式（待实现）
    JSON = "json"  # JSON格式


class ReportMetadata(BaseModel):
    """报告元数据"""

    report_id: str = Field(..., description="报告ID")
    analysis_id: str = Field(..., description="关联的分析ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str | None = Field(default=None, description="股票名称")

    # 文件信息
    file_path: Path | None = Field(default=None, description="文件路径")
    file_size_bytes: int | None = Field(default=None, description="文件大小")
    format: ReportFormat = Field(default=ReportFormat.HTML, description="报告格式")

    # 状态
    status: ReportStatus = Field(
        default=ReportStatus.GENERATING, description="报告状态"
    )
    error_message: str | None = Field(default=None, description="错误信息")

    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    expires_at: datetime | None = Field(
        default=None, description="过期时间（默认7天）"
    )

    # 访问信息
    access_count: int = Field(default=0, description="访问次数")
    last_accessed_at: datetime | None = Field(default=None, description="最后访问时间")

    model_config = {"arbitrary_types_allowed": True}


class ReportContent(BaseModel):
    """报告内容"""

    report_id: str = Field(..., description="报告ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str | None = Field(default=None, description="股票名称")

    # 分析结果
    analysis_data: dict[str, Any] = Field(..., description="分析数据")

    # 生成信息
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    generator_version: str = Field(default="1.0.0", description="生成器版本")

    model_config = {"frozen": False}


class ReportListResponse(BaseModel):
    """报告列表响应"""

    reports: list[ReportMetadata] = Field(default_factory=list, description="报告列表")
    total: int = Field(..., description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页数量")


class ReportGenerateRequest(BaseModel):
    """报告生成请求"""

    analysis_id: str = Field(..., description="分析ID")
    format: ReportFormat = Field(default=ReportFormat.HTML, description="报告格式")
    include_charts: bool = Field(default=False, description="是否包含图表")


class ReportStorageConfig(BaseModel):
    """报告存储配置"""

    base_path: Path = Field(default=Path("/tmp/reports"), description="存储基础路径")
    max_reports_per_stock: int = Field(default=10, description="每只股票最大报告数")
    retention_days: int = Field(default=7, description="报告保留天数")
    max_total_size_mb: int = Field(default=500, description="最大总存储空间(MB)")

    model_config = {"arbitrary_types_allowed": True}
