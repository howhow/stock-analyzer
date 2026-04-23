"""TestDataHubCircuitBreakerIntegration - 从 test_phase0_integration.py 迁移"""

from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from framework.data.circuit_breaker import CircuitBreaker
from framework.data.hub import DataHub, NoDataSourceAvailable
from framework.events import Events


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
            mock_df = pd.DataFrame({"close": [100.0, 101.0], "volume": [1000, 1100]})
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

            assert len(received) >= 1
            assert received[0]["source"] == "tushare"
        finally:
            Events.data_fetched.disconnect(on_fetched)


# ═══════════════════════════════════════════════════════════════
# Task 0.22: DCF 集成测试
# ═══════════════════════════════════════════════════════════════
