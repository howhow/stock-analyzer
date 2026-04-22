"""CircuitBreaker + DataHub 单元测试

测试目标:
- 熔断器状态机转换 (Closed → Open → HalfOpen → Closed)
- 失败计数与阈值
- Half-Open 试探逻辑
- DataHub 自动降级
- EventBus 事件集成
- 线程安全
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from framework.data.circuit_breaker import CircuitBreaker, CircuitState
from framework.data.hub import DataHub, NoDataSourceAvailable
from framework.events import Events


# ═══════════════════════════════════════════════════════════════
# CircuitBreaker 测试
# ═══════════════════════════════════════════════════════════════


class TestCircuitBreaker:
    """CircuitBreaker 核心功能测试"""

    def test_initial_state_is_closed(self):
        """测试初始状态为 Closed"""
        breaker = CircuitBreaker()
        assert breaker.get_state("tushare") == CircuitState.CLOSED

    def test_closed_allows_requests(self):
        """测试 Closed 状态允许请求"""
        breaker = CircuitBreaker()
        assert breaker.should_retry("tushare") is True

    def test_failure_count_increments(self):
        """测试失败计数递增"""
        breaker = CircuitBreaker(failure_threshold=3)
        breaker.record_failure("tushare")
        assert breaker.get_failure_count("tushare") == 1

    def test_transitions_to_open_after_threshold(self):
        """测试达到阈值后转为 Open"""
        breaker = CircuitBreaker(failure_threshold=3)

        # 连续失败 3 次
        for _ in range(3):
            breaker.record_failure("tushare")

        assert breaker.get_state("tushare") == CircuitState.OPEN
        assert breaker.should_retry("tushare") is False

    def test_success_resets_failure_count(self):
        """测试成功重置失败计数"""
        breaker = CircuitBreaker(failure_threshold=3)

        # 失败 2 次
        breaker.record_failure("tushare")
        breaker.record_failure("tushare")
        assert breaker.get_failure_count("tushare") == 2

        # 成功 1 次
        breaker.record_success("tushare")
        assert breaker.get_failure_count("tushare") == 0
        assert breaker.get_state("tushare") == CircuitState.CLOSED

    def test_open_to_half_open_after_timeout(self):
        """测试 Open 超时后转 Half-Open"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)

        # 熔断
        for _ in range(3):
            breaker.record_failure("tushare")
        assert breaker.get_state("tushare") == CircuitState.OPEN

        # 等待超时
        time.sleep(0.15)

        # 应该允许重试（转 Half-Open）
        assert breaker.should_retry("tushare") is True

    def test_half_open_success_transitions_to_closed(self):
        """测试 Half-Open 试探成功转 Closed"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)

        # 熔断
        for _ in range(3):
            breaker.record_failure("tushare")

        # 等待超时
        time.sleep(0.15)
        breaker.should_retry("tushare")  # 触发转 Half-Open

        # 试探成功
        breaker.record_success("tushare")
        assert breaker.get_state("tushare") == CircuitState.CLOSED

    def test_half_open_failure_transitions_to_open(self):
        """测试 Half-Open 试探失败转 Open"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)

        # 熔断
        for _ in range(3):
            breaker.record_failure("tushare")

        # 等待超时
        time.sleep(0.15)
        breaker.should_retry("tushare")  # 触发转 Half-Open

        # 试探失败
        breaker.record_failure("tushare")
        assert breaker.get_state("tushare") == CircuitState.OPEN

    def test_half_open_max_calls_limit(self):
        """测试 Half-Open 状态下试探次数限制"""
        breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=0.1, half_open_max_calls=1
        )

        # 熔断
        for _ in range(3):
            breaker.record_failure("tushare")

        # 等待超时
        time.sleep(0.15)

        # 第一次 should_retry 允许（消耗试探配额）
        assert breaker.should_retry("tushare") is True

        # 第二次 should_retry 拒绝（已达试探上限）
        assert breaker.should_retry("tushare") is False

    def test_independent_source_states(self):
        """测试不同数据源状态独立"""
        breaker = CircuitBreaker(failure_threshold=3)

        # tushare 熔断
        for _ in range(3):
            breaker.record_failure("tushare")

        # akshare 不受影响
        assert breaker.get_state("tushare") == CircuitState.OPEN
        assert breaker.get_state("akshare") == CircuitState.CLOSED
        assert breaker.should_retry("akshare") is True

    def test_reset_single_source(self):
        """测试重置单个数据源"""
        breaker = CircuitBreaker(failure_threshold=3)

        for _ in range(3):
            breaker.record_failure("tushare")
        assert breaker.get_state("tushare") == CircuitState.OPEN

        breaker.reset("tushare")
        assert breaker.get_state("tushare") == CircuitState.CLOSED
        assert breaker.get_failure_count("tushare") == 0

    def test_reset_all_sources(self):
        """测试重置所有数据源"""
        breaker = CircuitBreaker(failure_threshold=3)

        for _ in range(3):
            breaker.record_failure("tushare")
            breaker.record_failure("akshare")

        breaker.reset_all()
        assert breaker.get_state("tushare") == CircuitState.CLOSED
        assert breaker.get_state("akshare") == CircuitState.CLOSED

    def test_eventbus_integration_on_open(self):
        """测试熔断时发送 EventBus 事件"""
        breaker = CircuitBreaker(failure_threshold=2)
        received = []

        @Events.data_source_failed.connect
        def handler(sender, source, error, **kwargs):
            received.append({"source": source, "error": error})

        try:
            for _ in range(2):
                breaker.record_failure("tushare")

            assert len(received) >= 1
            assert received[-1]["source"] == "tushare"
            assert "Circuit breaker opened" in received[-1]["error"]
        finally:
            Events.data_source_failed.disconnect(handler)

    def test_eventbus_integration_on_recovery(self):
        """测试恢复时发送 EventBus 事件"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        recovered = []

        @Events.data_source_recovered.connect
        def handler(sender, source, **kwargs):
            recovered.append(source)

        try:
            # 熔断
            for _ in range(2):
                breaker.record_failure("tushare")

            # 等待超时 → Half-Open
            time.sleep(0.15)
            breaker.should_retry("tushare")

            # 试探成功 → Closed
            breaker.record_success("tushare")

            assert "tushare" in recovered
        finally:
            Events.data_source_recovered.disconnect(handler)


# ═══════════════════════════════════════════════════════════════
# DataHub 测试
# ═══════════════════════════════════════════════════════════════


def _make_source(name: str, priority: int, *, fail: bool = False):
    """创建 mock 数据源"""
    source = MagicMock()
    source.name = name
    source.priority = priority

    if fail:
        source.fetch_daily = AsyncMock(side_effect=ConnectionError(f"{name} down"))
    else:
        source.fetch_daily = AsyncMock(
            return_value=__import__("pandas").DataFrame(
                {"close": [100.0], "volume": [1000]}
            )
        )

    return source


class TestDataHub:
    """DataHub 核心功能测试"""

    @pytest.mark.asyncio
    async def test_fetch_daily_from_primary(self):
        """测试从主数据源获取数据"""
        primary = _make_source("tushare", priority=1)
        backup = _make_source("akshare", priority=2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_daily("600519.SH")

        assert len(df) == 1
        primary.fetch_daily.assert_called_once()
        backup.fetch_daily.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_to_backup_on_primary_failure(self):
        """测试主源失败自动降级到备用源"""
        primary = _make_source("tushare", priority=1, fail=True)
        backup = _make_source("akshare", priority=2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_daily("600519.SH")

        assert len(df) == 1
        primary.fetch_daily.assert_called_once()
        backup.fetch_daily.assert_called_once()

    @pytest.mark.asyncio
    async def test_raise_when_all_sources_fail(self):
        """测试所有数据源失败时抛出异常"""
        primary = _make_source("tushare", priority=1, fail=True)
        backup = _make_source("akshare", priority=2, fail=True)

        hub = DataHub(sources=[primary, backup])

        with pytest.raises(NoDataSourceAvailable, match="All sources failed"):
            await hub.fetch_daily("600519.SH")

    @pytest.mark.asyncio
    async def test_skip_circuit_broken_source(self):
        """测试跳过已熔断的数据源"""
        primary = _make_source("tushare", priority=1, fail=True)
        backup = _make_source("akshare", priority=2)

        breaker = CircuitBreaker(failure_threshold=1)
        hub = DataHub(sources=[primary, backup], breaker=breaker)

        # 第一次调用：primary 失败 → fallback to backup
        df1 = await hub.fetch_daily("600519.SH")
        assert len(df1) == 1

        # primary 已熔断（failure_threshold=1）
        assert breaker.get_state("tushare") == CircuitState.OPEN

        # 重置 primary mock 让它能成功
        primary.fetch_daily = AsyncMock(
            return_value=__import__("pandas").DataFrame({"close": [200.0]})
        )

        # 第二次调用：primary 已熔断，直接用 backup
        await hub.fetch_daily("600519.SH")
        primary.fetch_daily.assert_not_called()  # 跳过熔断源
        backup.fetch_daily.assert_called()

    @pytest.mark.asyncio
    async def test_get_source_status(self):
        """测试获取数据源状态"""
        primary = _make_source("tushare", priority=1)
        backup = _make_source("akshare", priority=2)

        hub = DataHub(sources=[primary, backup])
        status = hub.get_source_status()

        assert "tushare" in status
        assert "akshare" in status
        assert status["tushare"]["state"] == "closed"
        assert status["tushare"]["priority"] == 1
        assert status["akshare"]["priority"] == 2

    @pytest.mark.asyncio
    async def test_sources_sorted_by_priority(self):
        """测试数据源按优先级排序"""
        low_priority = _make_source("akshare", priority=2)
        high_priority = _make_source("tushare", priority=1)

        hub = DataHub(sources=[low_priority, high_priority])
        # 内部应该按 priority 排序
        assert hub._sources[0].name == "tushare"
        assert hub._sources[1].name == "akshare"
