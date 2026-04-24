"""Test DataHub financial data interfaces"""

from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from framework.data.circuit_breaker import CircuitBreaker
from framework.data.hub import DataHub, NoDataSourceAvailable
from framework.events import Events


class TestDataHubFinancial:
    """DataHub 财务数据接口测试"""

    def _create_mock_source(
        self, name: str, priority: int, should_fail: bool = False
    ) -> MagicMock:
        """创建 Mock 数据源"""
        source = MagicMock()
        source.name = name
        source.priority = priority

        if should_fail:
            source.fetch_financial = AsyncMock(side_effect=Exception(f"{name} 不可用"))
            source.fetch_income = AsyncMock(side_effect=Exception(f"{name} 不可用"))
            source.fetch_fina_indicator = AsyncMock(side_effect=Exception(f"{name} 不可用"))
        else:
            mock_financial = pd.DataFrame({
                "ts_code": ["600519.SH"],
                "pe": [30.5],
                "pb": [8.2],
            })
            mock_income = pd.DataFrame({
                "ts_code": ["600519.SH"],
                "total_revenue": [1500000000.0],
            })
            mock_fina = pd.DataFrame({
                "ts_code": ["600519.SH"],
                "roe": [15.5],
            })
            source.fetch_financial = AsyncMock(return_value=mock_financial)
            source.fetch_income = AsyncMock(return_value=mock_income)
            source.fetch_fina_indicator = AsyncMock(return_value=mock_fina)

        return source

    @pytest.mark.asyncio
    async def test_fetch_financial_primary_succeeds(self) -> None:
        """fetch_financial: 主数据源正常 → 直接返回"""
        primary = self._create_mock_source("tushare", 1)
        backup = self._create_mock_source("akshare", 2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_financial("600519.SH")

        assert df is not None
        assert df["pe"].iloc[0] == 30.5
        primary.fetch_financial.assert_called_once()
        backup.fetch_financial.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_financial_fallback(self) -> None:
        """fetch_financial: 主数据源失败 → 自动降级"""
        primary = self._create_mock_source("tushare", 1, should_fail=True)
        backup = self._create_mock_source("akshare", 2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_financial("600519.SH")

        assert df is not None
        assert df["pe"].iloc[0] == 30.5
        primary.fetch_financial.assert_called_once()
        backup.fetch_financial.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_income_primary_succeeds(self) -> None:
        """fetch_income: 主数据源正常 → 直接返回"""
        primary = self._create_mock_source("tushare", 1)
        backup = self._create_mock_source("akshare", 2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_income("600519.SH")

        assert df is not None
        assert df["total_revenue"].iloc[0] == 1500000000.0
        primary.fetch_income.assert_called_once()
        backup.fetch_income.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_income_fallback(self) -> None:
        """fetch_income: 主数据源失败 → 自动降级"""
        primary = self._create_mock_source("tushare", 1, should_fail=True)
        backup = self._create_mock_source("akshare", 2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_income("600519.SH")

        assert df is not None
        assert df["total_revenue"].iloc[0] == 1500000000.0
        primary.fetch_income.assert_called_once()
        backup.fetch_income.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_fina_indicator_primary_succeeds(self) -> None:
        """fetch_fina_indicator: 主数据源正常 → 直接返回"""
        primary = self._create_mock_source("tushare", 1)
        backup = self._create_mock_source("akshare", 2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_fina_indicator("600519.SH")

        assert df is not None
        assert df["roe"].iloc[0] == 15.5
        primary.fetch_fina_indicator.assert_called_once()
        backup.fetch_fina_indicator.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_fina_indicator_fallback(self) -> None:
        """fetch_fina_indicator: 主数据源失败 → 自动降级"""
        primary = self._create_mock_source("tushare", 1, should_fail=True)
        backup = self._create_mock_source("akshare", 2)

        hub = DataHub(sources=[primary, backup])
        df = await hub.fetch_fina_indicator("600519.SH")

        assert df is not None
        assert df["roe"].iloc[0] == 15.5
        primary.fetch_fina_indicator.assert_called_once()
        backup.fetch_fina_indicator.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_sources_fail_raises_error(self) -> None:
        """所有数据源失败 → 抛出 NoDataSourceAvailable"""
        primary = self._create_mock_source("tushare", 1, should_fail=True)
        backup = self._create_mock_source("akshare", 2, should_fail=True)

        hub = DataHub(sources=[primary, backup])
        with pytest.raises(NoDataSourceAvailable):
            await hub.fetch_financial("600519.SH")

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
        df1 = await hub.fetch_financial("600519.SH")
        assert df1 is not None

        # 第二次调用：primary 已熔断，直接走 backup
        df2 = await hub.fetch_financial("600519.SH")
        assert df2 is not None

        # primary 应该只被调用 1 次（熔断后跳过）
        assert primary.fetch_financial.call_count == 1

    @pytest.mark.asyncio
    async def test_data_fetched_event_sent(self) -> None:
        """数据获取成功后发送 data_fetched 事件"""
        primary = self._create_mock_source("tushare", 1)

        received: list[dict] = []

        @Events.data_fetched.connect
        def on_fetched(sender, **kwargs):
            received.append(kwargs)

        try:
            hub = DataHub(sources=[primary])
            await hub.fetch_financial("600519.SH")

            assert len(received) >= 1
            assert received[0]["source"] == "tushare"
        finally:
            Events.data_fetched.disconnect(on_fetched)
