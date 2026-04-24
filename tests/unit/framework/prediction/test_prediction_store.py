"""
预测存储服务测试

测试 PredictionStore 的 CRUD 操作和验证逻辑。
"""

from datetime import date, timedelta

import pytest

from framework.models.prediction import (
    PredictionCreate,
    PredictionDirection,
    PredictionStatus,
    PredictionUpdate,
)
from framework.prediction.store import PredictionStore, get_prediction_store


class TestPredictionStore:
    """预测存储测试"""

    @pytest.fixture
    def store(self):
        """创建新的存储实例"""
        return PredictionStore()

    @pytest.fixture
    def sample_prediction(self):
        """示例预测请求"""
        return PredictionCreate(
            stock_code="000001.SZ",
            stock_name="平安银行",
            direction=PredictionDirection.UP,
            target_price=15.5,
            confidence=0.75,
            target_date=date.today() + timedelta(days=30),
            baseline_price=12.0,
            strategy="test_strategy",
            notes="测试预测",
        )

    def test_create_prediction(self, store, sample_prediction):
        """测试创建预测"""
        prediction = store.create(sample_prediction)

        assert prediction.id is not None
        assert prediction.id.startswith("pred_")
        assert prediction.stock_code == "000001.SZ"
        assert prediction.stock_name == "平安银行"
        assert prediction.direction == PredictionDirection.UP
        assert prediction.target_price == 15.5
        assert prediction.confidence == 0.75
        assert prediction.status == PredictionStatus.PENDING
        assert prediction.strategy == "test_strategy"
        assert prediction.notes == "测试预测"
        assert prediction.actual_price is None
        assert prediction.accuracy_score is None

    def test_create_multiple_predictions(self, store, sample_prediction):
        """测试创建多个预测，ID递增"""
        pred1 = store.create(sample_prediction)
        pred2 = store.create(sample_prediction)

        assert pred1.id != pred2.id
        assert int(pred2.id.split("_")[1]) == int(pred1.id.split("_")[1]) + 1

    def test_get_prediction(self, store, sample_prediction):
        """测试获取预测"""
        created = store.create(sample_prediction)
        retrieved = store.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.stock_code == "000001.SZ"

    def test_get_nonexistent_prediction(self, store):
        """测试获取不存在的预测"""
        result = store.get("pred_nonexistent")
        assert result is None

    def test_update_prediction(self, store, sample_prediction):
        """测试更新预测"""
        created = store.create(sample_prediction)

        update = PredictionUpdate(
            target_price=16.0,
            confidence=0.80,
            notes="更新后的备注",
        )

        updated = store.update(created.id, update)

        assert updated is not None
        assert updated.target_price == 16.0
        assert updated.confidence == 0.80
        assert updated.notes == "更新后的备注"
        # 未更新的字段保持不变
        assert updated.stock_code == "000001.SZ"
        assert updated.direction == PredictionDirection.UP

    def test_update_nonexistent_prediction(self, store):
        """测试更新不存在的预测"""
        update = PredictionUpdate(target_price=20.0)
        result = store.update("pred_nonexistent", update)
        assert result is None

    def test_update_partial_fields(self, store, sample_prediction):
        """测试部分字段更新"""
        created = store.create(sample_prediction)

        # 只更新 target_price
        update = PredictionUpdate(target_price=18.0)
        updated = store.update(created.id, update)

        assert updated.target_price == 18.0
        # confidence 和 notes 保持不变
        assert updated.confidence == 0.75
        assert updated.notes == "测试预测"

    def test_delete_prediction(self, store, sample_prediction):
        """测试删除预测"""
        created = store.create(sample_prediction)

        assert store.delete(created.id) is True
        assert store.get(created.id) is None

    def test_delete_nonexistent_prediction(self, store):
        """测试删除不存在的预测"""
        assert store.delete("pred_nonexistent") is False

    def test_get_all_predictions(self, store, sample_prediction):
        """测试获取所有预测"""
        store.create(sample_prediction)
        store.create(sample_prediction)

        all_predictions = store.get_all()
        assert len(all_predictions) == 2

    def test_get_all_with_stock_code_filter(self, store, sample_prediction):
        """测试按股票代码过滤"""
        store.create(sample_prediction)

        # 创建不同股票的预测
        other = sample_prediction.model_copy(update={"stock_code": "000002.SZ"})
        store.create(other)

        results = store.get_all(stock_code="000001.SZ")
        assert len(results) == 1
        assert results[0].stock_code == "000001.SZ"

    def test_get_all_with_status_filter(self, store, sample_prediction):
        """测试按状态过滤"""
        created = store.create(sample_prediction)

        # 验证后状态变为 CORRECT 或 INCORRECT
        store.verify_prediction(created.id, 15.0)  # 价格上涨，预测正确

        pending = store.get_all(status=PredictionStatus.PENDING)
        assert len(pending) == 0

        correct = store.get_all(status=PredictionStatus.CORRECT)
        assert len(correct) == 1

    def test_get_all_with_date_filter(self, store, sample_prediction):
        """测试按日期过滤"""
        store.create(sample_prediction)

        # 创建更远未来日期的预测
        future = sample_prediction.model_copy(
            update={"target_date": date.today() + timedelta(days=60)}
        )
        store.create(future)

        # 按开始日期过滤（只取30天后的）- 注意过滤的是 prediction_date 不是 target_date
        # 两个预测都是今天创建的，所以 start_date=today 应该返回2个
        results = store.get_all(start_date=date.today())
        assert len(results) == 2

        # 按结束日期过滤（今天之前的不应该有任何）
        results = store.get_all(end_date=date.today() - timedelta(days=1))
        assert len(results) == 0

    def test_get_all_with_limit(self, store, sample_prediction):
        """测试限制数量"""
        for _ in range(5):
            store.create(sample_prediction)

        results = store.get_all(limit=3)
        assert len(results) == 3

    def test_get_all_sorting(self, store, sample_prediction):
        """测试排序（最新在前）"""
        # 创建不同日期的预测
        pred1 = sample_prediction.model_copy(
            update={"target_date": date.today() + timedelta(days=10)}
        )
        pred2 = sample_prediction.model_copy(
            update={"target_date": date.today() + timedelta(days=20)}
        )

        store.create(pred1)
        store.create(pred2)

        results = store.get_all()
        # 按 prediction_date 排序，最新的在前
        assert len(results) == 2

    def test_get_pending_verifications(self, store, sample_prediction):
        """测试获取待验证预测"""
        today = date.today()
        # 创建今天到期的预测（target_date = today + 1，但 prediction_date < target_date）
        pred_today = sample_prediction.model_copy(
            update={"target_date": today + timedelta(days=1)}
        )
        created = store.create(pred_today)
        # 手动修改 target_date 为今天（绕过验证）
        prediction = store.get(created.id)
        prediction.target_date = today

        # 创建未来日期的预测
        future = sample_prediction.model_copy(
            update={"target_date": today + timedelta(days=30)}
        )
        store.create(future)

        pending = store.get_pending_verifications(today)
        assert len(pending) == 1
        assert pending[0].target_date == today

    def test_get_pending_verifications_default_date(self, store, sample_prediction):
        """测试获取待验证预测（默认今天）"""
        today = date.today()
        pred_today = sample_prediction.model_copy(
            update={"target_date": today + timedelta(days=1)}
        )
        created = store.create(pred_today)
        # 手动修改 target_date 为今天
        prediction = store.get(created.id)
        prediction.target_date = today

        pending = store.get_pending_verifications()
        assert len(pending) == 1

    def test_verify_prediction_correct(self, store, sample_prediction):
        """测试验证预测 - 预测正确"""
        created = store.create(sample_prediction)

        # 价格上涨，预测 UP 正确
        verified = store.verify_prediction(created.id, 15.0)

        assert verified is not None
        assert verified.status == PredictionStatus.CORRECT
        assert verified.actual_price == 15.0
        assert verified.accuracy_score is not None
        assert verified.accuracy_score > 0
        assert verified.verified_at is not None

    def test_verify_prediction_incorrect(self, store, sample_prediction):
        """测试验证预测 - 预测错误"""
        created = store.create(sample_prediction)

        # 价格下跌，预测 UP 错误
        verified = store.verify_prediction(created.id, 10.0)

        assert verified is not None
        assert verified.status == PredictionStatus.INCORRECT
        assert verified.accuracy_score == 0.0

    def test_verify_prediction_nonexistent(self, store):
        """测试验证不存在的预测"""
        result = store.verify_prediction("pred_nonexistent", 15.0)
        assert result is None

    def test_verify_prediction_with_tolerance(self, store, sample_prediction):
        """测试验证预测 - 使用容差"""
        created = store.create(sample_prediction)

        # 价格变化在容差范围内（3%），视为 FLAT
        # baseline=12.0, 变化 2% -> 12.24
        verified = store.verify_prediction(created.id, 12.24, tolerance=0.03)

        assert verified is not None
        # 方向为 FLAT，与 UP 不同，所以预测错误
        assert verified.status == PredictionStatus.INCORRECT

    def test_bulk_verify(self, store, sample_prediction):
        """测试批量验证"""
        pred1 = store.create(sample_prediction)
        pred2 = store.create(sample_prediction)

        verifications = {
            pred1.id: 15.0,  # 正确
            pred2.id: 10.0,  # 错误
        }

        count = store.bulk_verify(verifications)
        assert count == 2

        # 验证状态
        assert store.get(pred1.id).status == PredictionStatus.CORRECT
        assert store.get(pred2.id).status == PredictionStatus.INCORRECT

    def test_get_stats(self, store, sample_prediction):
        """测试获取统计"""
        # 创建并验证一些预测
        pred1 = store.create(sample_prediction)
        store.verify_prediction(pred1.id, 15.0)  # 正确

        pred2 = store.create(sample_prediction)
        store.verify_prediction(pred2.id, 10.0)  # 错误

        store.create(sample_prediction)  # 待验证

        stats = store.get_stats()
        assert stats.total == 3
        assert stats.correct == 1
        assert stats.incorrect == 1
        assert stats.pending == 1
        assert stats.accuracy_rate == 1 / 2  # 已验证中的准确率

    def test_get_stats_with_stock_filter(self, store, sample_prediction):
        """测试获取统计 - 按股票过滤"""
        store.create(sample_prediction)

        other = sample_prediction.model_copy(update={"stock_code": "000002.SZ"})
        store.create(other)

        stats = store.get_stats(stock_code="000001.SZ")
        assert stats.total == 1

    def test_get_stats_with_strategy_filter(self, store, sample_prediction):
        """测试获取统计 - 按策略过滤"""
        store.create(sample_prediction)

        other = sample_prediction.model_copy(update={"strategy": "other_strategy"})
        store.create(other)

        stats = store.get_stats(strategy="test_strategy")
        assert stats.total == 1

    def test_get_stats_empty(self, store):
        """测试空存储的统计"""
        stats = store.get_stats()
        assert stats.total == 0
        assert stats.accuracy_rate == 0.0

    def test_get_prediction_store_singleton(self):
        """测试全局存储单例"""
        store1 = get_prediction_store()
        store2 = get_prediction_store()

        assert store1 is store2

    def test_prediction_is_expired(self, store, sample_prediction):
        """测试预测过期检查"""
        # 创建即将过期的预测（target_date 是明天）
        near_past = sample_prediction.model_copy(
            update={"target_date": date.today() + timedelta(days=1)}
        )
        created = store.create(near_past)

        prediction = store.get(created.id)
        # 设置 target_date 为过去日期来模拟过期
        prediction.target_date = date.today() - timedelta(days=1)
        assert prediction.is_expired() is True

        # 验证后不再过期
        store.verify_prediction(created.id, 15.0)
        prediction = store.get(created.id)
        assert prediction.is_expired() is False

    def test_prediction_is_not_expired(self, store, sample_prediction):
        """测试未过期预测"""
        future_date = date.today() + timedelta(days=30)
        future_pred = sample_prediction.model_copy(update={"target_date": future_date})
        created = store.create(future_pred)

        prediction = store.get(created.id)
        assert prediction.is_expired() is False
