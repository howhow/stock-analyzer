"""TestEventBusIntegration - 从 test_phase0_integration.py 迁移"""

import pytest

from framework.data.circuit_breaker import CircuitBreaker
from framework.events import Events


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
