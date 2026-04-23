"""EventBus 集成测试 — 端到端验证"""

import pytest

from framework.events import Events


@pytest.mark.integration
class TestEventBusIntegration:
    """EventBus 端到端集成测试"""

    def test_eventbus_end_to_end(self):
        """验证事件发送和接收完整流程"""
        received = []

        @Events.data_fetched.connect
        def handler(sender, **kwargs):
            received.append(kwargs)

        try:
            # 发送事件
            Events.data_fetched.send("test", source="tushare", symbol="688981.SH")

            # 验证接收
            assert len(received) == 1
            assert received[0]["source"] == "tushare"
        finally:
            Events.data_fetched.disconnect(handler)
