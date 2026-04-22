"""Phase 0 集成测试

验证目标:
- Task 0.20: EventBus 与现有模块集成
- Task 0.21: DataHub 熔断器端到端降级验证
- Task 0.22: DCF 真实股票估值测试
- Task 0.24: Phase 0 整体验收
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np
import pandas as pd

from framework.events import Events
from framework.data.circuit_breaker import CircuitBreaker
from framework.data.hub import DataHub, NoDataSourceAvailable
from framework.trading.seasons.dcf import DCFValuation, MonteCarloDCFResult


# ═══════════════════════════════════════════════════════════════
# Task 0.20: EventBus 集成测试
# ═══════════════════════════════════════════════════════════════


class TestEventBusIntegration:
    """EventBus 与现有模块集成验证"""

    def test_eventbus_signal_registration(self) -> None:
        """验证所有事件信号已注册"""
        # 所有架构文档定义的事件都必须存在
        required_events = [
            "season_changed",
            "dcf_calculated",
            "safety_margin_updated",
            "wuxing_state_changed",
            "transition_detected",
            "bayesian_updated",
            "position_plan_created",
            "stop_loss_triggered",
            "analysis_triggered",
            "alert_triggered",
            "data_source_failed",
            "data_source_recovered",
            "data_fetched",
        ]
        for event_name in required_events:
            assert hasattr(Events, event_name), f"事件 {event_name} 未注册"

    def test_eventbus_send_and_receive(self) -> None:
        """验证事件发送与接收"""
        received: list[dict] = []

        @Events.data_fetched.connect
        def on_data_fetched(sender, **kwargs):
            received.append(kwargs)

        try:
            # blinker sender 是位置参数，不能用作关键字参数
            Events.data_fetched.send("test", source="tushare", symbol="600519.SH")
            assert len(received) == 1
            assert received[0]["source"] == "tushare"
            assert received[0]["symbol"] == "600519.SH"
        finally:
            Events.data_fetched.disconnect(on_data_fetched)

    def test_eventbus_data_source_failed_integration(self) -> None:
        """验证 data_source_failed 事件与 CircuitBreaker 集成"""
        received: list[dict] = []

        @Events.data_source_failed.connect
        def on_failed(sender, **kwargs):
            received.append(kwargs)

        try:
            breaker = CircuitBreaker(failure_threshold=2)
            # 第一次失败
            breaker.record_failure("tushare")
            # 第二次失败触发熔断，CircuitBreaker 内部会发送 data_source_failed 事件
            breaker.record_failure("tushare")

            # 验证事件被发送（至少一次）
            assert len(received) >= 1
            # 最后一条应该是熔断触发
            assert received[-1]["source"] == "tushare"
        finally:
            Events.data_source_failed.disconnect(on_failed)

    def test_eventbus_multiple_subscribers(self) -> None:
        """验证多订阅者接收同一事件"""
        log1: list[str] = []
        log2: list[str] = []

        @Events.alert_triggered.connect
        def subscriber1(sender, **kwargs):
            log1.append(kwargs.get("level", ""))

        @Events.alert_triggered.connect
        def subscriber2(sender, **kwargs):
            log2.append(kwargs.get("level", ""))

        try:
            Events.alert_triggered.send("test", level="critical", msg="测试")
            assert log1 == ["critical"]
            assert log2 == ["critical"]
        finally:
            Events.alert_triggered.disconnect(subscriber1)
            Events.alert_triggered.disconnect(subscriber2)


# ═══════════════════════════════════════════════════════════════
# Task 0.21: DataHub 熔断器端到端降级验证
# ═══════════════════════════════════════════════════════════════


class TestDataHubCircuitBreakerIntegration:
    """DataHub + CircuitBreaker 端到端降级验证"""

    def _create_mock_source(
        self, name: str, priority: int, should_fail: bool = False
    ) -> MagicMock:
        """创建 Mock 数据源"""
        source = MagicMock()
        source.name = name
        source.priority = priority

        if should_fail:
            source.fetch_daily = AsyncMock(side_effect=Exception(f"{name} 不可用"))
        else:
            mock_df = pd.DataFrame(
                {"close": [100.0, 101.0], "volume": [1000, 1100]}
            )
            source.fetch_daily = AsyncMock(return_value=mock_df)

        return source

    @pytest.mark.asyncio
    async def test_primary_source_succeeds(self) -> None:
        """主数据源正常 → 直接返回"""
        primary = self._create_mock_source("tushare", 1)
        backup = self._create_mock_source("akshare", 2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_daily("600519.SH")

        assert df is not None
        primary.fetch_daily.assert_called_once()
        backup.fetch_daily.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_to_backup_on_primary_failure(self) -> None:
        """主数据源失败 → 自动降级到备用源"""
        primary = self._create_mock_source("tushare", 1, should_fail=True)
        backup = self._create_mock_source("akshare", 2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_daily("600519.SH")

        assert df is not None
        primary.fetch_daily.assert_called_once()
        backup.fetch_daily.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_sources_fail_raises_error(self) -> None:
        """所有数据源失败 → 抛出 NoDataSourceAvailable"""
        primary = self._create_mock_source("tushare", 1, should_fail=True)
        backup = self._create_mock_source("akshare", 2, should_fail=True)

        hub = DataHub(sources=[primary, backup])
        with pytest.raises(NoDataSourceAvailable):
            await hub.fetch_daily("600519.SH")

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_failed_source(self) -> None:
        """熔断器触发后跳过已熔断的数据源"""
        primary = self._create_mock_source("tushare", 1, should_fail=True)
        backup = self._create_mock_source("akshare", 2)

        hub = DataHub(
            sources=[primary, backup],
            breaker=CircuitBreaker(failure_threshold=1),
        )

        # 第一次调用：primary 失败 1 次，触发熔断，fallback 到 backup
        df1 = await hub.fetch_daily("600519.SH")
        assert df1 is not None

        # 第二次调用：primary 已熔断，直接走 backup
        df2 = await hub.fetch_daily("600519.SH")
        assert df2 is not None

        # primary 应该只被调用 1 次（熔断后跳过）
        assert primary.fetch_daily.call_count == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self) -> None:
        """熔断器恢复后重新尝试数据源"""
        primary = self._create_mock_source("tushare", 1)
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)

        # 手动熔断
        breaker.record_failure("tushare")
        assert not breaker.should_retry("tushare")

        # 等待恢复
        import time

        time.sleep(0.02)

        # 半开状态允许重试
        assert breaker.should_retry("tushare")

    @pytest.mark.asyncio
    async def test_data_fetched_event_sent_on_success(self) -> None:
        """数据获取成功后发送 data_fetched 事件"""
        primary = self._create_mock_source("tushare", 1)

        received: list[dict] = []

        @Events.data_fetched.connect
        def on_fetched(sender, **kwargs):
            received.append(kwargs)

        try:
            hub = DataHub(sources=[primary])
            await hub.fetch_daily("600519.SH")

            assert len(received) == 1
            assert received[0]["source"] == "tushare"
        finally:
            Events.data_fetched.disconnect(on_fetched)


# ═══════════════════════════════════════════════════════════════
# Task 0.22: DCF 集成测试
# ═══════════════════════════════════════════════════════════════


class TestDCFIntegration:
    """DCF 蒙特卡洛估值集成测试"""

    def test_monte_carlo_dcf_basic(self) -> None:
        """测试蒙特卡洛 DCF 基本流程"""
        dcf = DCFValuation()

        # 构造测试数据
        current_fcf = 40.0  # 当前 FCF（亿元）
        shares_outstanding = 12.56  # 总股本（亿股）

        result = dcf.calculate_monte_carlo(
            current_fcf=current_fcf,
            shares_outstanding=shares_outstanding,
            industry="消费",
            simulations=500,
        )

        # 验证结果结构
        assert isinstance(result, MonteCarloDCFResult)
        assert result.mean > 0
        assert result.median > 0
        assert len(result.ci_95) == 2
        assert result.ci_95[0] < result.ci_95[1]
        assert len(result.distribution) == 500

    def test_monte_carlo_dcf_industry_discount_rates(self) -> None:
        """测试不同行业折现率影响"""
        dcf = DCFValuation()

        current_fcf = 40.0
        shares_outstanding = 12.56

        result_bank = dcf.calculate_monte_carlo(
            current_fcf=current_fcf,
            shares_outstanding=shares_outstanding,
            industry="银行",
            simulations=200,
        )
        result_tech = dcf.calculate_monte_carlo(
            current_fcf=current_fcf,
            shares_outstanding=shares_outstanding,
            industry="科技",
            simulations=200,
        )

        # 科技行业折现率更高，估值应该更低
        assert result_bank.mean > result_tech.mean

    def test_dcf_calculated_event(self) -> None:
        """测试 DCF 计算完成后发送 dcf_calculated 事件"""
        received: list[dict] = []

        @Events.dcf_calculated.connect
        def on_dcf(sender, **kwargs):
            received.append(kwargs)

        try:
            dcf = DCFValuation()
            dcf.calculate_monte_carlo(
                current_fcf=40.0,
                shares_outstanding=12.56,
                industry="消费",
                simulations=100,
            )

            assert len(received) >= 1
        finally:
            Events.dcf_calculated.disconnect(on_dcf)

    def test_dcf_performance_local_calculation(self) -> None:
        """测试 DCF 本地计算性能 < 3s"""
        import time

        dcf = DCFValuation()

        start = time.time()
        result = dcf.calculate_monte_carlo(
            current_fcf=40.0,
            shares_outstanding=12.56,
            industry="消费",
            simulations=1000,
        )
        elapsed = time.time() - start

        # 本地计算 < 3s
        assert elapsed < 3.0, f"DCF 计算 {elapsed:.2f}s 超过 3s 限制"


# ═══════════════════════════════════════════════════════════════
# Task 0.24: Phase 0 验收
# ═══════════════════════════════════════════════════════════════


class TestPhase0Acceptance:
    """Phase 0 整体验收"""

    def test_eventbus_module_exists(self) -> None:
        """验证 EventBus 模块存在且可导入"""
        from framework.events import Events

        assert Events is not None

    def test_circuit_breaker_module_exists(self) -> None:
        """验证 CircuitBreaker 模块存在且可导入"""
        from framework.data.circuit_breaker import CircuitBreaker

        assert CircuitBreaker is not None

    def test_datahub_module_exists(self) -> None:
        """验证 DataHub 模块存在且可导入"""
        from framework.data.hub import DataHub

        assert DataHub is not None

    def test_dcf_module_exists(self) -> None:
        """验证 DCF 模块存在且可导入"""
        from framework.trading.seasons.dcf import DCFValuation

        assert DCFValuation is not None

    def test_all_eventbus_signals_connected(self) -> None:
        """验证所有 EventBus 信号可正常工作"""
        signals = [
            Events.season_changed,
            Events.dcf_calculated,
            Events.safety_margin_updated,
            Events.data_source_failed,
            Events.data_source_recovered,
            Events.data_fetched,
        ]

        for signal in signals:
            # 每个信号都应能发送和接收
            received: list[dict] = []

            @signal.connect
            def handler(sender, **kwargs):
                received.append(kwargs)

            try:
                signal.send("test", **{"key": "value"})
                assert len(received) == 1
            finally:
                signal.disconnect(handler)
