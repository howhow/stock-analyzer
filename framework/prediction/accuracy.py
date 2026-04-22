"""
准确率计算器

计算预测的准确率和相关统计。
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from structlog import get_logger

from framework.models.prediction import (
    Prediction,
    PredictionDirection,
    PredictionStats,
    PredictionStatus,
)

logger = get_logger(__name__)


class AccuracyCalculator:
    """
    准确率计算器

    提供多种准确率计算方法。
    """

    @staticmethod
    def calculate_simple_accuracy(
        predictions: list[Prediction],
        tolerance: float = 0.03,
    ) -> float:
        """
        简单准确率计算

        Args:
            predictions: 预测列表（已验证）
            tolerance: 价格变化容差

        Returns:
            准确率（0-1）
        """
        verified = [p for p in predictions if p.status != PredictionStatus.PENDING]
        if not verified:
            return 0.0

        correct = sum(1 for p in verified if p.status == PredictionStatus.CORRECT)
        return correct / len(verified)

    @staticmethod
    def calculate_weighted_accuracy(
        predictions: list[Prediction],
        weight_by_confidence: bool = True,
    ) -> float:
        """
        加权准确率计算

        Args:
            predictions: 预测列表
            weight_by_confidence: 是否按置信度加权

        Returns:
            加权准确率（0-1）
        """
        verified = [p for p in predictions if p.status != PredictionStatus.PENDING]
        if not verified:
            return 0.0

        total_weight = 0.0
        weighted_correct = 0.0

        for p in verified:
            weight = p.confidence if weight_by_confidence else 1.0
            total_weight += weight

            if p.status == PredictionStatus.CORRECT:
                weighted_correct += weight

        return weighted_correct / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def calculate_by_direction(
        predictions: list[Prediction],
    ) -> dict[PredictionDirection, dict[str, float | int]]:
        """
        按方向统计准确率

        Args:
            predictions: 预测列表

        Returns:
            按方向分组的统计数据
        """
        stats: dict[PredictionDirection, dict[str, float | int]] = defaultdict(
            lambda: {"total": 0, "correct": 0, "accuracy": 0.0}
        )

        for p in predictions:
            if p.status == PredictionStatus.PENDING:
                continue

            stats[p.direction]["total"] += 1
            if p.status == PredictionStatus.CORRECT:
                stats[p.direction]["correct"] += 1

        # 计算准确率
        for direction, data in stats.items():
            if data["total"] > 0:
                data["accuracy"] = data["correct"] / data["total"]

        return dict(stats)

    @staticmethod
    def calculate_stats(
        predictions: list[Prediction],
    ) -> PredictionStats:
        """
        计算完整统计

        Args:
            predictions: 预测列表

        Returns:
            统计结果
        """
        total = len(predictions)
        if total == 0:
            return PredictionStats(
                total=0,
                correct=0,
                incorrect=0,
                pending=0,
                accuracy_rate=0.0,
                avg_confidence=0.0,
                up_correct=0,
                down_correct=0,
                flat_correct=0,
            )

        correct = sum(1 for p in predictions if p.status == PredictionStatus.CORRECT)
        incorrect = sum(
            1 for p in predictions if p.status == PredictionStatus.INCORRECT
        )
        pending = sum(1 for p in predictions if p.status == PredictionStatus.PENDING)

        verified = correct + incorrect
        accuracy_rate = correct / verified if verified > 0 else 0.0

        # 计算平均置信度
        confidences = [p.confidence for p in predictions]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # 按方向统计正确数
        up_correct = sum(
            1
            for p in predictions
            if p.direction == PredictionDirection.UP
            and p.status == PredictionStatus.CORRECT
        )
        down_correct = sum(
            1
            for p in predictions
            if p.direction == PredictionDirection.DOWN
            and p.status == PredictionStatus.CORRECT
        )
        flat_correct = sum(
            1
            for p in predictions
            if p.direction == PredictionDirection.FLAT
            and p.status == PredictionStatus.CORRECT
        )

        return PredictionStats(
            total=total,
            correct=correct,
            incorrect=incorrect,
            pending=pending,
            accuracy_rate=accuracy_rate,
            avg_confidence=avg_confidence,
            up_correct=up_correct,
            down_correct=down_correct,
            flat_correct=flat_correct,
        )

    @staticmethod
    def calculate_time_series_accuracy(
        predictions: list[Prediction],
        period_days: int = 7,
    ) -> list[dict[str, Any]]:
        """
        计算时间序列准确率

        Args:
            predictions: 预测列表
            period_days: 统计周期（天）

        Returns:
            按时间段的准确率列表
        """
        if not predictions:
            return []

        # 按验证日期分组
        by_period: dict[date, list[Prediction]] = defaultdict(list)

        for p in predictions:
            if p.verified_at:
                period_date = p.verified_at.date()
                by_period[period_date].append(p)

        # 计算每个周期的准确率
        results: list[dict[str, Any]] = []
        for period_date, period_predictions in sorted(by_period.items()):
            verified = [
                p for p in period_predictions if p.status != PredictionStatus.PENDING
            ]

            if not verified:
                continue

            correct = sum(1 for p in verified if p.status == PredictionStatus.CORRECT)
            accuracy = correct / len(verified)

            results.append(
                {
                    "date": period_date.isoformat(),
                    "total": len(verified),
                    "correct": correct,
                    "accuracy": accuracy,
                }
            )

        return results


class AccuracyRanker:
    """
    准确率排行榜

    计算预测准确率排行榜。
    """

    @staticmethod
    def rank_by_stock(
        predictions: list[Prediction],
        min_predictions: int = 3,
    ) -> list[dict[str, Any]]:
        """
        按股票排名准确率

        Args:
            predictions: 预测列表
            min_predictions: 最小预测数（少于此数不计入排行）

        Returns:
            排行榜列表
        """
        # 按股票分组
        by_stock: dict[str, list[Prediction]] = defaultdict(list)
        for p in predictions:
            by_stock[p.stock_code].append(p)

        # 计算每只股票的准确率
        rankings: list[dict[str, Any]] = []
        for stock_code, stock_predictions in by_stock.items():
            verified = [
                p for p in stock_predictions if p.status != PredictionStatus.PENDING
            ]

            if len(verified) < min_predictions:
                continue

            correct = sum(1 for p in verified if p.status == PredictionStatus.CORRECT)
            accuracy = correct / len(verified)

            stock_name = verified[0].stock_name if verified else None

            rankings.append(
                {
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "total_predictions": len(verified),
                    "correct": correct,
                    "accuracy": accuracy,
                }
            )

        # 按准确率排序
        rankings.sort(key=lambda x: (-x["accuracy"], -x["total_predictions"]))

        return rankings

    @staticmethod
    def rank_by_strategy(
        predictions: list[Prediction],
        min_predictions: int = 5,
    ) -> list[dict[str, Any]]:
        """
        按策略排名准确率

        Args:
            predictions: 预测列表
            min_predictions: 最小预测数

        Returns:
            排行榜列表
        """
        # 按策略分组
        by_strategy: dict[str, list[Prediction]] = defaultdict(list)
        for p in predictions:
            if p.strategy:
                by_strategy[p.strategy].append(p)

        # 计算每个策略的准确率
        rankings: list[dict[str, Any]] = []
        for strategy, strategy_predictions in by_strategy.items():
            verified = [
                p for p in strategy_predictions if p.status != PredictionStatus.PENDING
            ]

            if len(verified) < min_predictions:
                continue

            correct = sum(1 for p in verified if p.status == PredictionStatus.CORRECT)
            accuracy = correct / len(verified)

            rankings.append(
                {
                    "strategy": strategy,
                    "total_predictions": len(verified),
                    "correct": correct,
                    "accuracy": accuracy,
                }
            )

        # 按准确率排序
        rankings.sort(key=lambda x: (-x["accuracy"], -x["total_predictions"]))

        return rankings

    @staticmethod
    def rank_by_period(
        predictions: list[Prediction],
        days: int = 30,
    ) -> dict[str, Any]:
        """
        计算最近 N 天的排行榜

        Args:
            predictions: 预测列表
            days: 天数

        Returns:
            排行榜数据
        """
        cutoff_date = date.today() - timedelta(days=days)

        recent_predictions = [
            p for p in predictions if p.prediction_date >= cutoff_date
        ]

        stats = AccuracyCalculator.calculate_stats(recent_predictions)

        return {
            "period_days": days,
            "total_predictions": stats.total,
            "correct": stats.correct,
            "accuracy": stats.accuracy_rate,
            "by_direction": AccuracyCalculator.calculate_by_direction(
                recent_predictions
            ),
        }
