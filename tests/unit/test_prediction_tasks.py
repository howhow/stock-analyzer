"""
预测验证任务测试

测试预测验证相关的 Celery 任务。
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.tasks.prediction_tasks import (
    calculate_accuracy_stats_task,
    cleanup_expired_predictions_task,
    generate_rankings_task,
    verify_predictions_task,
)
from framework.models.prediction import PredictionStatus


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_prediction():
    """创建模拟预测对象"""
    prediction = MagicMock()
    prediction.id = "pred_001"
    prediction.baseline_price = 100.0
    return prediction


@pytest.fixture
def mock_store(mock_prediction):
    """创建模拟预测存储"""
    store = MagicMock()
    store.get_pending_verifications.return_value = [mock_prediction]
    store.bulk_verify.return_value = 1
    store.list.return_value = [mock_prediction]
    return store


# ============================================================
# verify_predictions_task
# ============================================================


class TestVerifyPredictionsTask:
    """测试预测验证任务"""

    @patch("app.tasks.prediction_tasks.get_prediction_store")
    def test_verify_predictions_success(self, mock_get_store, mock_store, mock_prediction):
        """测试正常验证"""
        mock_get_store.return_value = mock_store

        result = verify_predictions_task()

        assert result["verified"] == 1
        assert result["total"] == 1
        mock_store.get_pending_verifications.assert_called_once_with(date.today())
        mock_store.bulk_verify.assert_called_once()

    @patch("app.tasks.prediction_tasks.get_prediction_store")
    def test_verify_predictions_empty(self, mock_get_store):
        """测试空预测列表"""
        store = MagicMock()
        store.get_pending_verifications.return_value = []
        mock_get_store.return_value = store

        result = verify_predictions_task()

        assert result["verified"] == 0
        assert result["message"] == "No pending predictions"


# ============================================================
# calculate_accuracy_stats_task
# ============================================================


class TestCalculateAccuracyStatsTask:
    """测试准确率统计任务"""

    @patch("app.tasks.prediction_tasks.get_prediction_store")
    @patch("app.tasks.prediction_tasks.AccuracyCalculator")
    def test_calculate_stats_success(self, mock_calc_class, mock_get_store):
        """测试正常计算"""
        store = MagicMock()
        store.list.return_value = []
        mock_get_store.return_value = store

        mock_stats = MagicMock()
        mock_stats.total = 100
        mock_stats.correct = 75
        mock_stats.accuracy_rate = 0.75
        mock_calc_class.calculate_stats.return_value = mock_stats

        result = calculate_accuracy_stats_task()

        assert result["total"] == 100
        assert result["correct"] == 75
        assert result["accuracy"] == 0.75


# ============================================================
# generate_rankings_task
# ============================================================


class TestGenerateRankingsTask:
    """测试排行榜生成任务"""

    @patch("app.tasks.prediction_tasks.get_prediction_store")
    @patch("app.tasks.prediction_tasks.AccuracyRanker")
    def test_generate_rankings_success(self, mock_ranker_class, mock_get_store):
        """测试正常生成"""
        store = MagicMock()
        store.list.return_value = []
        mock_get_store.return_value = store

        mock_ranker_class.rank_by_stock.return_value = [
            {"stock": "600519.SH", "accuracy": 0.85},
            {"stock": "000001.SZ", "accuracy": 0.80},
        ]
        mock_ranker_class.rank_by_strategy.return_value = [
            {"strategy": "momentum", "accuracy": 0.82},
        ]

        result = generate_rankings_task()

        assert "stock_rankings" in result
        assert "strategy_rankings" in result
        assert len(result["stock_rankings"]) == 2
        assert len(result["strategy_rankings"]) == 1


# ============================================================
# cleanup_expired_predictions_task
# ============================================================


class TestCleanupExpiredPredictionsTask:
    """测试清理过期预测任务"""

    @patch("app.tasks.prediction_tasks.get_prediction_store")
    def test_cleanup_no_expired(self, mock_get_store):
        """测试无过期预测"""
        store = MagicMock()
        prediction = MagicMock()
        prediction.is_expired.return_value = False
        store.list.return_value = [prediction]
        mock_get_store.return_value = store

        result = cleanup_expired_predictions_task()

        assert result["expired"] == 0

    @patch("app.tasks.prediction_tasks.get_prediction_store")
    def test_cleanup_with_expired(self, mock_get_store):
        """测试有过期预测"""
        store = MagicMock()
        prediction = MagicMock()
        prediction.is_expired.return_value = True
        store.list.return_value = [prediction]
        mock_get_store.return_value = store

        result = cleanup_expired_predictions_task()

        assert result["expired"] == 1
        assert prediction.status == PredictionStatus.EXPIRED
