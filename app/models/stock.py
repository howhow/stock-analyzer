"""
股票数据模型

定义股票相关的数据结构
"""

from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field, field_validator


def validate_stock_code(v: str) -> str:
    """
    验证股票代码格式
    
    支持格式: 600519.SH, 000001.SZ, 00700.HK
    
    Args:
        v: 股票代码字符串
    
    Returns:
        验证后的股票代码（大写）
    
    Raises:
        ValueError: 格式无效
    """
    if not v:
        raise ValueError("stock code cannot be empty")
    
    parts = v.split(".")
    if len(parts) != 2:
        raise ValueError(f"invalid stock code format: {v}")
    
    code, market = parts
    
    if not code.isdigit() or len(code) != 6:
        raise ValueError(f"invalid stock code: {code}")
    
    if market.upper() not in ("SH", "SZ", "HK"):
        raise ValueError(f"invalid market: {market}")
    
    return v.upper()


# Pydantic v2: 使用 BeforeValidator
StockCode = Annotated[str, BeforeValidator(validate_stock_code)]


class StockInfo(BaseModel):
    """股票基本信息"""

    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场: SH/SZ/HK")
    industry: str | None = Field(default=None, description="所属行业")
    list_date: date | None = Field(default=None, description="上市日期")

    model_config = {"frozen": True}


class DailyQuote(BaseModel):
    """日线行情数据"""

    stock_code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    open: float = Field(..., gt=0, description="开盘价")
    close: float = Field(..., gt=0, description="收盘价")
    high: float = Field(..., gt=0, description="最高价")
    low: float = Field(..., gt=0, description="最低价")
    volume: float = Field(..., ge=0, description="成交量(手)")
    amount: float = Field(..., ge=0, description="成交额(千元)")
    turnover_rate: float | None = Field(default=None, description="换手率(%)")

    @field_validator("high")
    @classmethod
    def validate_high(cls, v: float, info: Any) -> float:
        """最高价必须 >= 最低价"""
        low = info.data.get("low")
        if low is not None and v < low:
            raise ValueError(f"high ({v}) must be >= low ({low})")
        return v

    model_config = {"frozen": True}


class IntradayQuote(BaseModel):
    """分钟线行情数据"""

    stock_code: str = Field(..., description="股票代码")
    trade_time: datetime = Field(..., description="交易时间")
    open: float = Field(..., gt=0, description="开盘价")
    close: float = Field(..., gt=0, description="收盘价")
    high: float = Field(..., gt=0, description="最高价")
    low: float = Field(..., gt=0, description="最低价")
    volume: float = Field(..., ge=0, description="成交量(手)")
    amount: float = Field(..., ge=0, description="成交额(千元)")

    model_config = {"frozen": True}


class FinancialData(BaseModel):
    """财务数据"""

    stock_code: str = Field(..., description="股票代码")
    report_date: date = Field(..., description="报告期")
    revenue: float | None = Field(default=None, description="营业收入(元)")
    net_profit: float | None = Field(default=None, description="净利润(元)")
    total_assets: float | None = Field(default=None, description="总资产(元)")
    total_liabilities: float | None = Field(default=None, description="总负债(元)")
    roe: float | None = Field(default=None, description="净资产收益率(%)")
    pe_ratio: float | None = Field(default=None, description="市盈率")
    pb_ratio: float | None = Field(default=None, description="市净率")
    debt_ratio: float | None = Field(default=None, description="资产负债率(%)")

    model_config = {"frozen": True}


class StockDataPoint(BaseModel):
    """股票数据点（用于分析）"""

    stock_code: str
    trade_date: date
    close: float
    volume: float
    ma5: float | None = None
    ma10: float | None = None
    ma20: float | None = None
    ema5: float | None = None
    ema20: float | None = None

    model_config = {"frozen": True}
