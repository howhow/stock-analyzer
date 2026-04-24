"""
标准行情数据模型

定义所有数据源插件返回的标准数据格式。
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_serializer


class StandardQuote(BaseModel):
    """
    标准行情数据模型

    所有数据源插件返回的数据必须转换为此格式，
    确保上层应用可以使用统一的数据结构。
    """

    # 基本信息
    code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")

    # 价格信息
    open: float | None = Field(None, description="开盘价")
    high: float | None = Field(None, description="最高价")
    low: float | None = Field(None, description="最低价")
    close: float = Field(..., description="收盘价（必填）")
    adj_close: float | None = Field(None, description="复权价格")

    # 成交信息
    volume: int | None = Field(None, description="成交量")
    amount: float | None = Field(None, description="成交额")
    turnover_rate: float | None = Field(None, description="换手率")

    # 数据质量字段
    source: str = Field(..., description="数据源名称")
    completeness: float = Field(1.0, description="数据完整度（0-1）")
    quality_score: float = Field(1.0, description="数据质量评分（0-1）")

    # 元数据
    currency: Literal["CNY", "USD", "HKD"] = Field("CNY", description="货币")

    model_config = {
        "frozen": False,
        "extra": "ignore",
    }

    @field_serializer("trade_date")
    def serialize_trade_date(self, value: date) -> str:
        """序列化日期为 ISO 格式字符串"""
        return value.isoformat()

    def is_complete(self) -> bool:
        """检查数据是否完整（所有价格和成交字段都有值）"""
        # 检查必填字段
        if not all(
            getattr(self, f) is not None for f in ["code", "trade_date", "close"]
        ):
            return False
        # 检查价格字段（open, high, low 都要有值）
        if self.open is None or self.high is None or self.low is None:
            return False
        return True

    def is_valid(self) -> bool:
        """检查数据是否合理（价格逻辑正确）"""
        # 如果没有价格数据，返回 False
        if self.open is None or self.high is None or self.low is None:
            return False
        # 最高价 >= 最低价
        if self.high < self.low:
            return False
        # 收盘价在最高价和最低价之间
        if not (self.low <= self.close <= self.high):
            return False
        return True

    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump()

    def get_quality_label(self) -> str:
        """获取质量标签"""
        if self.quality_score >= 0.9:
            return "high"
        elif self.quality_score >= 0.7:
            return "medium"
        else:
            return "low"


class StandardQuoteBatch(BaseModel):
    """标准行情数据批次（多日数据）"""

    code: str = Field(..., description="股票代码")
    quotes: list[StandardQuote] = Field(..., description="行情数据列表")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    source: str = Field(..., description="数据源")

    model_config = {"populate_by_name": True}

    @property
    def count(self) -> int:
        """数据条数"""
        return len(self.quotes)

    def get_first_quote(self) -> StandardQuote | None:
        """获取第一条数据"""
        return self.quotes[0] if self.quotes else None

    def get_last_quote(self) -> StandardQuote | None:
        """获取最后一条数据"""
        return self.quotes[-1] if self.quotes else None

    def to_dataframe(self):
        """转换为 pandas DataFrame"""
        import pandas as pd

        if not self.quotes:
            return None

        data = {
            "date": [q.trade_date for q in self.quotes],
            "open": [q.open for q in self.quotes],
            "high": [q.high for q in self.quotes],
            "low": [q.low for q in self.quotes],
            "close": [q.close for q in self.quotes],
            "volume": [q.volume for q in self.quotes],
        }
        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df
