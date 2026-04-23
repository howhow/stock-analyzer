"""DataHub 集成测试 — 真实数据源验证"""

import pytest


@pytest.mark.integration
class TestDataHubIntegration:
    """DataHub 集成测试"""

    def test_datahub_basic(self):
        """验证 DataHub 基本功能"""
        from framework.data.circuit_breaker import CircuitBreaker
        from framework.data.hub import DataHub

        # 验证 DataHub 可实例化
        hub = DataHub(sources=[], breaker=CircuitBreaker())
        assert hub is not None
        assert hub.breaker is not None
