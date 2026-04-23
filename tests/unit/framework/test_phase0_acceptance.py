"""TestPhase0Acceptance - 从 test_phase0_integration.py 迁移"""

import pytest

from framework.data.circuit_breaker import CircuitBreaker
from framework.data.hub import DataHub
from framework.events import Events
from framework.trading.seasons.dcf import DCFValuation


class TestPhase0Acceptance:
    """Phase 0 整体验收"""

    def test_eventbus_module_exists(self) -> None:
        """验证 EventBus 模块存在且可导入"""
        assert Events is not None

    def test_circuit_breaker_module_exists(self) -> None:
        """验证 CircuitBreaker 模块存在且可导入"""
        assert CircuitBreaker is not None

    def test_datahub_module_exists(self) -> None:
        """验证 DataHub 模块存在且可导入"""
        assert DataHub is not None

    def test_dcf_module_exists(self) -> None:
        """验证 DCF 模块存在且可导入"""
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
