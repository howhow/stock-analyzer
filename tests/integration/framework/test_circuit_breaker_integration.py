"""熔断器集成测试 — 真实降级验证"""

import pytest

from framework.data.circuit_breaker import CircuitBreaker


@pytest.mark.integration
class TestCircuitBreakerIntegration:
    """熔断器真实降级集成测试"""

    def test_circuit_breaker_real_failure(self):
        """验证熔断器在真实失败场景下工作"""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1.0,
        )

        # 记录失败
        breaker.record_failure("test_source")
        assert breaker.should_retry("test_source")  # 第一次允许重试

        breaker.record_failure("test_source")
        assert not breaker.should_retry("test_source")  # 第二次熔断
