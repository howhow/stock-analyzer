"""
预测存储服务

提供预测数据的 CRUD 操作。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from structlog import get_logger

from framework.models.prediction import (
    Prediction,
    PredictionCreate,
    PredictionStats,
    PredictionStatus,
    PredictionUpdate,
)

logger = get_logger(__name__)


class PredictionStore:
    """
    预测存储

    提供预测数据的持久化操作。
    目前使用内存存储，可扩展为数据库存储。
    """

    def __init__(self):
        """初始化存储"""
        self._predictions: dict[str, Prediction] = {}
        self._next_id: int = 1

    def create(self, request: PredictionCreate) -> Prediction:
        """
        创建预测

        Args:
            request: 创建请求

        Returns:
            创建的预测
        """
        prediction_id = f"pred_{self._next_id}"
        self._next_id += 1

        prediction = Prediction(
            id=prediction_id,
            stock_code=request.stock_code,
            stock_name=request.stock_name,
            direction=request.direction,
            target_price=request.target_price,
            confidence=request.confidence,
            prediction_date=date.today(),
            target_date=request.target_date,
            baseline_price=request.baseline_price,
            strategy=request.strategy,
            notes=request.notes,
            source=request.source,
            status=PredictionStatus.PENDING,
            actual_price=None,
            accuracy_score=None,
            verified_at=None,
        )

        self._predictions[prediction_id] = prediction

        logger.info(
            "prediction_created",
            id=prediction_id,
            stock_code=request.stock_code,
            direction=request.direction.value,
        )

        return prediction

    def get(self, prediction_id: str) -> Prediction | None:
        """
        获取预测

        Args:
            prediction_id: 预测 ID

        Returns:
            预测，不存在返回 None
        """
        return self._predictions.get(prediction_id)

    def update(
        self,
        prediction_id: str,
        request: PredictionUpdate,
    ) -> Prediction | None:
        """
        更新预测

        Args:
            prediction_id: 预测 ID
            request: 更新请求

        Returns:
            更新后的预测，不存在返回 None
        """
        prediction = self._predictions.get(prediction_id)
        if not prediction:
            return None

        # 更新字段
        if request.target_price is not None:
            prediction.target_price = request.target_price
        if request.confidence is not None:
            prediction.confidence = request.confidence
        if request.notes is not None:
            prediction.notes = request.notes

        prediction.updated_at = datetime.now()

        logger.info("prediction_updated", id=prediction_id)

        return prediction

    def delete(self, prediction_id: str) -> bool:
        """
        删除预测

        Args:
            prediction_id: 预测 ID

        Returns:
            是否成功
        """
        if prediction_id in self._predictions:
            del self._predictions[prediction_id]
            logger.info("prediction_deleted", id=prediction_id)
            return True
        return False

    def get_all(
        self,
        stock_code: str | None = None,
        status: PredictionStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
    ) -> list[Prediction]:
        """
        列出预测

        Args:
            stock_code: 股票代码过滤
            status: 状态过滤
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大数量

        Returns:
            预测列表
        """
        predictions = list(self._predictions.values())

        # 过滤
        if stock_code:
            predictions = [p for p in predictions if p.stock_code == stock_code]
        if status:
            predictions = [p for p in predictions if p.status == status]
        if start_date:
            predictions = [p for p in predictions if p.prediction_date >= start_date]
        if end_date:
            predictions = [p for p in predictions if p.prediction_date <= end_date]

        # 按预测日期排序（最新在前）
        predictions.sort(key=lambda p: p.prediction_date, reverse=True)

        return predictions[:limit]

    def get_pending_verifications(
        self, target_date: date | None = None
    ) -> list[Prediction]:
        """
        获取待验证的预测

        Args:
            target_date: 目标日期（默认今天）

        Returns:
            待验证的预测列表
        """
        ref_date = target_date or date.today()

        return [
            p
            for p in self._predictions.values()
            if p.target_date == ref_date and p.status == PredictionStatus.PENDING
        ]

    def get_stats(
        self,
        stock_code: str | None = None,
        strategy: str | None = None,
    ) -> PredictionStats:
        """
        获取统计

        Args:
            stock_code: 股票代码过滤
            strategy: 策略过滤

        Returns:
            统计结果
        """
        predictions = self.get_all(stock_code=stock_code, limit=1000)

        if strategy:
            predictions = [p for p in predictions if p.strategy == strategy]

        from framework.prediction.accuracy import AccuracyCalculator

        return AccuracyCalculator.calculate_stats(predictions)

    def verify_prediction(
        self,
        prediction_id: str,
        actual_price: float,
        tolerance: float = 0.03,
    ) -> Prediction | None:
        """
        验证预测

        Args:
            prediction_id: 预测 ID
            actual_price: 实际价格
            tolerance: 容差

        Returns:
            验证后的预测，不存在返回 None
        """
        prediction = self._predictions.get(prediction_id)
        if not prediction:
            return None

        prediction.verify(actual_price, tolerance)

        logger.info(
            "prediction_verified",
            id=prediction_id,
            status=prediction.status.value,
            accuracy=prediction.accuracy_score,
        )

        return prediction

    def bulk_verify(
        self,
        verifications: dict[str, float],
        tolerance: float = 0.03,
    ) -> int:
        """
        批量验证

        Args:
            verifications: 预测ID -> 实际价格 映射
            tolerance: 容差

        Returns:
            成功验证的数量
        """
        count = 0
        for prediction_id, actual_price in verifications.items():
            if self.verify_prediction(prediction_id, actual_price, tolerance):
                count += 1

        logger.info("bulk_verify_completed", count=count, total=len(verifications))
        return count


# 全局存储实例
_store: PredictionStore | None = None


def get_prediction_store() -> PredictionStore:
    """获取全局存储实例"""
    global _store
    if _store is None:
        _store = PredictionStore()
    return _store
