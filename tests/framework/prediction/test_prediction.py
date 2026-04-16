"""
预测验证体系测试

测试预测模型、准确率计算和存储。
"""

import pytest
from datetime import date, timedelta

from framework.models.prediction import (
    Prediction,
    PredictionCreate,
    PredictionDirection,
    PredictionStatus,
    PredictionStats,
)
from framework.prediction import (
    AccuracyCalculator,
    AccuracyRanker,
    PredictionStore,
)


# ============================================================
# Prediction Model Tests
# ============================================================


class TestPredictionModel:
    """预测模型测试"""

    def test_create_prediction(self):
        """测试创建预测"""
        prediction = Prediction(
            stock_code="600519.SH",
            direction=PredictionDirection.UP,
            prediction_date=date.today(),
            target_date=date.today() + timedelta(days=7),
            baseline_price=1500.0,
            confidence=0.8,
        )

        assert prediction.stock_code == "600519.SH"
        assert prediction.direction == PredictionDirection.UP
        assert prediction.status == PredictionStatus.PENDING

    def test_prediction_validation(self):
        """测试预测验证"""
        # 目标日期必须大于预测日期
        with pytest.raises(ValueError):
            Prediction(
                stock_code="600519.SH",
                direction=PredictionDirection.UP,
                prediction_date=date.today(),
                target_date=date.today(),  # 错误：相同日期
                baseline_price=1500.0,
            )

    def test_calculate_accuracy_correct(self):
        """测试准确率计算 - 正确"""
        prediction = Prediction(
            stock_code="600519.SH",
            direction=PredictionDirection.UP,
            prediction_date=date.today(),
            target_date=date.today() + timedelta(days=7),
            baseline_price=100.0,
            confidence=0.8,
        )

        # 实际价格上涨 5%（超过 3% 容差）
        status, accuracy = prediction.calculate_accuracy(105.0, tolerance=0.03)

        assert status == PredictionStatus.CORRECT
        assert accuracy > 0

    def test_calculate_accuracy_incorrect(self):
        """测试准确率计算 - 错误"""
        prediction = Prediction(
            stock_code="600519.SH",
            direction=PredictionDirection.UP,
            prediction_date=date.today(),
            target_date=date.today() + timedelta(days=7),
            baseline_price=100.0,
            confidence=0.8,
        )

        # 实际价格下跌 5%
        status, accuracy = prediction.calculate_accuracy(95.0, tolerance=0.03)

        assert status == PredictionStatus.INCORRECT
        assert accuracy == 0.0

    def test_verify_prediction(self):
        """测试验证预测"""
        prediction = Prediction(
            stock_code="600519.SH",
            direction=PredictionDirection.UP,
            prediction_date=date.today(),
            target_date=date.today() + timedelta(days=7),
            baseline_price=100.0,
            confidence=0.8,
        )

        prediction.verify(105.0)

        assert prediction.status != PredictionStatus.PENDING
        assert prediction.actual_price == 105.0
        assert prediction.verified_at is not None

    def test_is_expired(self):
        """测试过期判断"""
        prediction = Prediction(
            stock_code="600519.SH",
            direction=PredictionDirection.UP,
            prediction_date=date.today() - timedelta(days=14),
            target_date=date.today() - timedelta(days=7),
            baseline_price=100.0,
        )

        assert prediction.is_expired() is True


# ============================================================
# Accuracy Calculator Tests
# ============================================================


class TestAccuracyCalculator:
    """准确率计算器测试"""

    def test_simple_accuracy(self):
        """测试简单准确率"""
        predictions = [
            Prediction(
                stock_code="600519.SH",
                direction=PredictionDirection.UP,
                prediction_date=date.today(),
                target_date=date.today() + timedelta(days=1),
                baseline_price=100.0,
                status=PredictionStatus.CORRECT,
            ),
            Prediction(
                stock_code="000001.SZ",
                direction=PredictionDirection.DOWN,
                prediction_date=date.today(),
                target_date=date.today() + timedelta(days=1),
                baseline_price=100.0,
                status=PredictionStatus.INCORRECT,
            ),
        ]

        accuracy = AccuracyCalculator.calculate_simple_accuracy(predictions)
        assert accuracy == 0.5

    def test_calculate_stats(self):
        """测试统计计算"""
        predictions = [
            Prediction(
                stock_code="600519.SH",
                direction=PredictionDirection.UP,
                prediction_date=date.today(),
                target_date=date.today() + timedelta(days=1),
                baseline_price=100.0,
                status=PredictionStatus.CORRECT,
                confidence=0.8,
            ),
            Prediction(
                stock_code="000001.SZ",
                direction=PredictionDirection.DOWN,
                prediction_date=date.today(),
                target_date=date.today() + timedelta(days=1),
                baseline_price=100.0,
                status=PredictionStatus.INCORRECT,
                confidence=0.6,
            ),
            Prediction(
                stock_code="000002.SZ",
                direction=PredictionDirection.UP,
                prediction_date=date.today(),
                target_date=date.today() + timedelta(days=1),
                baseline_price=100.0,
                status=PredictionStatus.PENDING,
                confidence=0.7,
            ),
        ]

        stats = AccuracyCalculator.calculate_stats(predictions)

        assert stats.total == 3
        assert stats.correct == 1
        assert stats.incorrect == 1
        assert stats.pending == 1
        assert stats.accuracy_rate == 0.5

    def test_calculate_by_direction(self):
        """测试按方向统计"""
        predictions = [
            Prediction(
                stock_code="600519.SH",
                direction=PredictionDirection.UP,
                prediction_date=date.today(),
                target_date=date.today() + timedelta(days=1),
                baseline_price=100.0,
                status=PredictionStatus.CORRECT,
            ),
            Prediction(
                stock_code="000001.SZ",
                direction=PredictionDirection.DOWN,
                prediction_date=date.today(),
                target_date=date.today() + timedelta(days=1),
                baseline_price=100.0,
                status=PredictionStatus.CORRECT,
            ),
            Prediction(
                stock_code="000002.SZ",
                direction=PredictionDirection.UP,
                prediction_date=date.today(),
                target_date=date.today() + timedelta(days=1),
                baseline_price=100.0,
                status=PredictionStatus.INCORRECT,
            ),
        ]

        by_direction = AccuracyCalculator.calculate_by_direction(predictions)

        assert PredictionDirection.UP in by_direction
        assert PredictionDirection.DOWN in by_direction
        assert by_direction[PredictionDirection.UP]["accuracy"] == 0.5


# ============================================================
# Prediction Store Tests
# ============================================================


class TestPredictionStore:
    """预测存储测试"""

    def test_create_prediction(self):
        """测试创建预测"""
        store = PredictionStore()
        request = PredictionCreate(
            stock_code="600519.SH",
            direction=PredictionDirection.UP,
            target_date=date.today() + timedelta(days=7),
            baseline_price=1500.0,
            confidence=0.8,
        )

        prediction = store.create(request)

        assert prediction.id is not None
        assert prediction.stock_code == "600519.SH"
        assert prediction.status == PredictionStatus.PENDING

    def test_get_prediction(self):
        """测试获取预测"""
        store = PredictionStore()
        request = PredictionCreate(
            stock_code="600519.SH",
            direction=PredictionDirection.UP,
            target_date=date.today() + timedelta(days=7),
            baseline_price=1500.0,
        )

        created = store.create(request)
        retrieved = store.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_predictions(self):
        """测试列出预测"""
        store = PredictionStore()

        for i in range(3):
            store.create(
                PredictionCreate(
                    stock_code=f"60051{i}.SH",
                    direction=PredictionDirection.UP,
                    target_date=date.today() + timedelta(days=7),
                    baseline_price=1500.0,
                )
            )

        predictions = store.get_all()

        assert len(predictions) == 3

    def test_verify_prediction(self):
        """测试验证预测"""
        store = PredictionStore()
        request = PredictionCreate(
            stock_code="600519.SH",
            direction=PredictionDirection.UP,
            target_date=date.today() + timedelta(days=7),
            baseline_price=100.0,
        )

        created = store.create(request)
        verified = store.verify_prediction(created.id, 105.0)

        assert verified is not None
        assert verified.status != PredictionStatus.PENDING
        assert verified.actual_price == 105.0


# ============================================================
# Accuracy Ranker Tests
# ============================================================


class TestAccuracyRanker:
    """排行榜测试"""

    def test_rank_by_stock(self):
        """测试按股票排名"""
        predictions = []

        # 股票 A：2 正确，1 错误
        for i, status in enumerate(
            [
                PredictionStatus.CORRECT,
                PredictionStatus.CORRECT,
                PredictionStatus.INCORRECT,
            ]
        ):
            predictions.append(
                Prediction(
                    stock_code="600519.SH",
                    direction=PredictionDirection.UP,
                    prediction_date=date.today(),
                    target_date=date.today() + timedelta(days=1),
                    baseline_price=100.0,
                    status=status,
                )
            )

        # 股票 B：1 正确
        predictions.append(
            Prediction(
                stock_code="000001.SZ",
                direction=PredictionDirection.UP,
                prediction_date=date.today(),
                target_date=date.today() + timedelta(days=1),
                baseline_price=100.0,
                status=PredictionStatus.CORRECT,
            )
        )

        rankings = AccuracyRanker.rank_by_stock(predictions, min_predictions=1)

        assert len(rankings) == 2
        # 股票 B 准确率 100%，应排第一
        assert rankings[0]["stock_code"] == "000001.SZ"
        assert rankings[0]["accuracy"] == 1.0
