"""
预测模型定义

定义股票预测的数据结构和验证逻辑。
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PredictionDirection(str, Enum):
    """预测方向"""
    UP = "up"      # 看涨
    DOWN = "down"  # 看跌
    FLAT = "flat"  # 持平


class PredictionStatus(str, Enum):
    """预测状态"""
    PENDING = "pending"      # 待验证
    CORRECT = "correct"      # 正确
    INCORRECT = "incorrect"  # 错误
    EXPIRED = "expired"      # 已过期（无数据验证）


class Prediction(BaseModel):
    """
    预测模型
    
    记录对某只股票的价格预测。
    """
    
    # 基本信息
    id: str | None = None
    stock_code: str = Field(..., description="股票代码")
    stock_name: str | None = Field(None, description="股票名称")
    
    # 预测内容
    direction: PredictionDirection = Field(..., description="预测方向")
    target_price: float | None = Field(None, description="目标价格")
    confidence: float = Field(0.5, ge=0, le=1, description="置信度")
    
    # 时间范围
    prediction_date: date = Field(..., description="预测日期")
    target_date: date = Field(..., description="目标日期（预测验证日期）")
    
    # 基准数据
    baseline_price: float = Field(..., gt=0, description="基准价格（预测时的价格）")
    
    # 验证结果
    status: PredictionStatus = Field(PredictionStatus.PENDING, description="验证状态")
    actual_price: float | None = Field(None, description="实际价格")
    accuracy_score: float | None = Field(None, ge=0, le=1, description="准确率得分")
    
    # 元数据
    source: str = Field("manual", description="预测来源")
    strategy: str | None = Field(None, description="预测策略")
    notes: str | None = Field(None, description="备注")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    verified_at: datetime | None = Field(None, description="验证时间")
    
    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: date, info: Any) -> date:
        """验证目标日期必须大于预测日期"""
        prediction_date = info.data.get("prediction_date")
        if prediction_date and v <= prediction_date:
            raise ValueError("目标日期必须大于预测日期")
        return v
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """验证置信度范围"""
        if not 0 <= v <= 1:
            raise ValueError("置信度必须在 0-1 之间")
        return v
    
    def calculate_accuracy(
        self,
        actual_price: float,
        tolerance: float = 0.03,
    ) -> tuple[PredictionStatus, float]:
        """
        计算预测准确率
        
        Args:
            actual_price: 实际价格
            tolerance: 容差范围（默认3%）
            
        Returns:
            (状态, 准确率得分)
        """
        # 计算价格变化
        price_change_pct = (actual_price - self.baseline_price) / self.baseline_price
        
        # 判断实际方向
        if price_change_pct > tolerance:
            actual_direction = PredictionDirection.UP
        elif price_change_pct < -tolerance:
            actual_direction = PredictionDirection.DOWN
        else:
            actual_direction = PredictionDirection.FLAT
        
        # 判断预测是否正确
        is_correct = actual_direction == self.direction
        
        # 计算准确率得分
        if is_correct:
            # 基于置信度计算得分
            accuracy = self.confidence
            status = PredictionStatus.CORRECT
        else:
            # 预测错误，得分为0
            accuracy = 0.0
            status = PredictionStatus.INCORRECT
        
        # 如果有目标价格，进一步计算精确度
        if self.target_price and is_correct:
            # 计算价格误差
            price_error = abs(actual_price - self.target_price) / self.target_price
            # 误差越小，得分越高（误差0时满分，误差20%时得0.5分）
            precision_bonus = max(0, 0.5 * (1 - price_error / 0.2))
            accuracy = min(1.0, accuracy + precision_bonus)
        
        return status, accuracy
    
    def verify(
        self,
        actual_price: float,
        tolerance: float = 0.03,
    ) -> None:
        """
        验证预测
        
        Args:
            actual_price: 实际价格
            tolerance: 容差范围
        """
        status, accuracy = self.calculate_accuracy(actual_price, tolerance)
        
        self.status = status
        self.actual_price = actual_price
        self.accuracy_score = accuracy
        self.verified_at = datetime.now()
        self.updated_at = datetime.now()
    
    def is_expired(self, reference_date: date | None = None) -> bool:
        """
        检查预测是否过期
        
        Args:
            reference_date: 参考日期（默认今天）
            
        Returns:
            是否过期
        """
        ref_date = reference_date or date.today()
        return ref_date > self.target_date and self.status == PredictionStatus.PENDING


class PredictionCreate(BaseModel):
    """创建预测请求"""
    
    stock_code: str
    stock_name: str | None = None
    direction: PredictionDirection
    target_price: float | None = None
    confidence: float = Field(0.5, ge=0, le=1)
    target_date: date
    baseline_price: float = Field(..., gt=0)
    source: str = "manual"
    strategy: str | None = None
    notes: str | None = None


class PredictionUpdate(BaseModel):
    """更新预测请求"""
    
    target_price: float | None = None
    confidence: float | None = Field(None, ge=0, le=1)
    notes: str | None = None


class PredictionStats(BaseModel):
    """预测统计"""
    
    total: int = Field(0, description="总预测数")
    correct: int = Field(0, description="正确预测数")
    incorrect: int = Field(0, description="错误预测数")
    pending: int = Field(0, description="待验证预测数")
    
    accuracy_rate: float = Field(0.0, ge=0, le=1, description="准确率")
    avg_confidence: float = Field(0.0, ge=0, le=1, description="平均置信度")
    
    up_correct: int = Field(0, description="看涨正确数")
    down_correct: int = Field(0, description="看跌正确数")
    flat_correct: int = Field(0, description="持平正确数")
    
    @property
    def wrong(self) -> int:
        """错误预测数（兼容旧代码）"""
        return self.incorrect
