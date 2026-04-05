import pytest
"""
熔断器单元测试
"""

import asyncio


from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitState,
)


class TestCircuitBreaker:
    """熔断器测试"""

    def test_initial_state(self):
        """测试初始状态"""
        breaker = CircuitBreaker(name="test")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed is True
        assert breaker.is_open is False

    @pytest.mark.asyncio
    async def test_record_success(self):
        """测试记录成功"""
        breaker = CircuitBreaker(name="test")
        await breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0

    @pytest.mark.asyncio
    async def test_open_after_threshold(self):
        """测试达到阈值后熔断"""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        # 记录3次失败
        for _ in range(3):
            await breaker.record_failure()

        assert breaker.state == CircuitState.OPEN
        assert breaker.is_open is True

    @pytest.mark.asyncio
    async def test_cannot_execute_when_open(self):
        """测试熔断状态拒绝请求"""
        breaker = CircuitBreaker(name="test", failure_threshold=2)

        # 触发熔断
        await breaker.record_failure()
        await breaker.record_failure()

        # 熔断器打开，拒绝请求
        can_exec = await breaker.can_execute()
        assert can_exec is False

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self):
        """测试超时后进入半开状态"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            timeout_seconds=0,  # 立即超时
        )

        # 触发熔断
        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # 等待超时
        await asyncio.sleep(0.1)

        # 可以执行（进入半开）
        can_exec = await breaker.can_execute()
        assert can_exec is True
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_recover_from_half_open(self):
        """测试从半开状态恢复"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            timeout_seconds=0,
            success_threshold=1,
        )

        # 触发熔断
        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # 等待超时进入半开
        await asyncio.sleep(0.1)
        await breaker.can_execute()
        assert breaker.state == CircuitState.HALF_OPEN

        # 记录成功，恢复
        await breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopen_from_half_open(self):
        """测试半开状态下失败重新熔断"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            timeout_seconds=0,
        )

        # 触发熔断
        await breaker.record_failure()
        await asyncio.sleep(0.1)
        await breaker.can_execute()  # 进入半开

        # 半开状态下失败，立即熔断
        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_call_success(self):
        """测试通过熔断器调用成功"""

        async def success_func():
            return "success"

        breaker = CircuitBreaker(name="test")
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_call_failure(self):
        """测试通过熔断器调用失败"""

        async def fail_func():
            raise ValueError("test error")

        breaker = CircuitBreaker(name="test", failure_threshold=1)

        with pytest.raises(ValueError):
            await breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_call_when_open(self):
        """测试熔断状态下调用抛异常"""
        breaker = CircuitBreaker(name="test", failure_threshold=1)
        await breaker.record_failure()

        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(lambda: "test")


class TestCircuitBreakerRegistry:
    """熔断器注册表测试"""

    def test_singleton(self):
        """测试单例模式"""
        r1 = CircuitBreakerRegistry()
        r2 = CircuitBreakerRegistry()
        assert r1 is r2

    def test_get_or_create(self):
        """测试获取或创建熔断器"""
        registry = CircuitBreakerRegistry()
        registry.reset_all()

        breaker1 = registry.get_or_create("test1")
        assert breaker1 is not None
        assert breaker1.name == "test1"

        # 再次获取同一个
        breaker2 = registry.get_or_create("test1")
        assert breaker1 is breaker2

    def test_get_all_status(self):
        """测试获取所有状态"""
        registry = CircuitBreakerRegistry()
        registry.reset_all()

        registry.get_or_create("test1")
        registry.get_or_create("test2")

        status = registry.get_all_status()
        assert "test1" in status
        assert "test2" in status

    def test_reset_all(self):
        """测试重置所有"""
        registry = CircuitBreakerRegistry()

        breaker = registry.get_or_create("test_reset")
        import asyncio

        asyncio.run(breaker.record_failure())

        registry.reset_all()

        assert breaker.state == CircuitState.CLOSED
