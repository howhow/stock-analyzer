"""
预测验证任务

Celery 任务：每日验证预测结果。
"""

from __future__ import annotations

from datetime import date

from structlog import get_logger

logger = get_logger(__name__)

# 模块级别导入，便于测试时 mock
from framework.models.prediction import PredictionStatus
from framework.prediction import (
    AccuracyCalculator,
    AccuracyRanker,
    get_prediction_store,
)


def verify_predictions_task():
    """
    Celery 任务：验证今日到期预测

    此任务应在每日收盘后运行。
    """
    store = get_prediction_store()
    pending = store.get_pending_verifications(date.today())

    if not pending:
        logger.info("no_pending_predictions")
        return {"verified": 0, "message": "No pending predictions"}

    # 获取实际价格（这里需要对接数据源）
    # 简化版本：使用模拟数据
    verifications: dict[str, float] = {}

    for prediction in pending:
        # TODO: 从数据源获取实际收盘价
        # 目前使用模拟价格
        mock_price = prediction.baseline_price * 1.01
        verifications[prediction.id] = mock_price

    # 批量验证
    verified_count = store.bulk_verify(verifications)

    logger.info("predictions_verified", count=verified_count)

    return {
        "verified": verified_count,
        "total": len(pending),
    }


def calculate_accuracy_stats_task():
    """
    Celery 任务：计算准确率统计

    定期更新统计数据。
    """
    store = get_prediction_store()
    predictions = store.list(limit=10000)

    stats = AccuracyCalculator.calculate_stats(predictions)

    logger.info(
        "accuracy_stats_calculated",
        total=stats.total,
        correct=stats.correct,
        accuracy=stats.accuracy_rate,
    )

    return {
        "total": stats.total,
        "correct": stats.correct,
        "accuracy": stats.accuracy_rate,
    }


def generate_rankings_task():
    """
    Celery 任务：生成排行榜

    定期生成预测准确率排行榜。
    """
    store = get_prediction_store()
    predictions = store.list(limit=10000)

    stock_rankings = AccuracyRanker.rank_by_stock(predictions)
    strategy_rankings = AccuracyRanker.rank_by_strategy(predictions)

    logger.info(
        "rankings_generated",
        stocks=len(stock_rankings),
        strategies=len(strategy_rankings),
    )

    return {
        "stock_rankings": stock_rankings[:10],
        "strategy_rankings": strategy_rankings[:10],
    }


def cleanup_expired_predictions_task():
    """
    Celery 任务：清理过期预测

    将超过验证日期且无数据的预测标记为过期。
    """
    store = get_prediction_store()
    predictions = store.list(status=PredictionStatus.PENDING, limit=10000)

    expired_count = 0
    for prediction in predictions:
        if prediction.is_expired():
            prediction.status = PredictionStatus.EXPIRED
            prediction.updated_at = date.today()
            expired_count += 1

    logger.info("expired_predictions_cleaned", count=expired_count)

    return {"expired": expired_count}
