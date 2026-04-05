"""
Health Check 完整测试
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.data.health_check import HealthChecker, HealthStatus
from app.data.base import BaseDataSource


class MockDataSource(BaseDataSource):
    """Mock数据源"""

    def __init__(self, name: str, is_healthy: bool = True, timeout: int = 10):
        super().__init__(name=name, timeout=timeout)
        self._is_healthy = is_healthy
        self.health_check_called = False

    async def get_stock_info(self, stock_code: str):
        return None

    async def get_daily_quotes(self, stock_code: str, start_date, end_date):
        return []

    async def get_intraday_quotes(self, stock_code: str):
        return []

    async def get_financial_data(self, stock_code: str):
        return None

    async def health_check(self) -> bool:
        self.health_check_called = True
        return self._is_healthy


class TestHealthCheckerComplete:
    """HealthChecker完整测试"""

    @pytest.fixture
    def health_checker(self):
        """创建健康检查器"""
        return HealthChecker(check_interval=60)

    @pytest.mark.asyncio
    async def test_check_healthy_source(self, health_checker):
        """测试健康的数据源"""
        source = MockDataSource("test", is_healthy=True)

        status = await health_checker.check_source(source)

        assert status.is_healthy is True
        assert status.source_name == "test"
        assert status.response_time_ms >= 0
        assert source.health_check_called is True

    @pytest.mark.asyncio
    async def test_check_unhealthy_source(self, health_checker):
        """测试不健康的数据源"""
        source = MockDataSource("test", is_healthy=False)

        status = await health_checker.check_source(source)

        assert status.is_healthy is False
        assert status.error_message is None

    @pytest.mark.asyncio
    async def test_check_all_sources(self, health_checker):
        """测试检查所有数据源"""
        sources = [
            MockDataSource("source1", is_healthy=True),
            MockDataSource("source2", is_healthy=False),
            MockDataSource("source3", is_healthy=True),
        ]

        results = await health_checker.check_all(sources)

        assert len(results) == 3
        assert results["source1"].is_healthy is True
        assert results["source2"].is_healthy is False
        assert results["source3"].is_healthy is True

    @pytest.mark.asyncio
    async def test_cached_status(self, health_checker):
        """测试缓存的状态"""
        source = MockDataSource("test", is_healthy=True)

        # 第一次检查
        await health_checker.check_source(source)

        # 第二次应该使用缓存
        cached = health_checker.get_cached_status("test")
        assert cached is not None
        assert cached.is_healthy is True

    @pytest.mark.asyncio
    async def test_force_check(self, health_checker):
        """测试强制检查"""
        source = MockDataSource("test", is_healthy=True)

        # 第一次检查
        await health_checker.check_source(source)

        # 强制重新检查
        source._is_healthy = False
        status = await health_checker.check_source(source, force=True)

        assert status.is_healthy is False

    def test_get_all_cached_status(self, health_checker):
        """测试获取所有缓存状态"""
        # 手动添加缓存
        health_checker._status_cache = {
            "source1": HealthStatus(
                source_name="source1",
                is_healthy=True,
                response_time_ms=10,
                last_check_time=datetime.now(),
            ),
            "source2": HealthStatus(
                source_name="source2",
                is_healthy=False,
                response_time_ms=20,
                last_check_time=datetime.now(),
            ),
        }

        all_status = health_checker.get_all_cached_status()

        assert len(all_status) == 2
        assert "source1" in all_status
        assert "source2" in all_status

    def test_clear_cache(self, health_checker):
        """测试清除缓存"""
        health_checker._status_cache = {
            "source1": HealthStatus(
                source_name="source1",
                is_healthy=True,
                response_time_ms=10,
                last_check_time=datetime.now(),
            ),
        }

        health_checker.clear_cache()

        assert len(health_checker._status_cache) == 0

    def test_get_healthy_sources(self, health_checker):
        """测试获取健康的数据源列表"""
        sources = [
            MockDataSource("source1", is_healthy=True),
            MockDataSource("source2", is_healthy=False),
            MockDataSource("source3", is_healthy=True),
        ]

        # 设置缓存
        health_checker._status_cache = {
            "source1": HealthStatus(
                source_name="source1",
                is_healthy=True,
                response_time_ms=10,
                last_check_time=datetime.now(),
            ),
            "source2": HealthStatus(
                source_name="source2",
                is_healthy=False,
                response_time_ms=20,
                last_check_time=datetime.now(),
            ),
            "source3": HealthStatus(
                source_name="source3",
                is_healthy=True,
                response_time_ms=15,
                last_check_time=datetime.now(),
            ),
        }

        healthy = health_checker.get_healthy_sources(sources)

        assert len(healthy) == 2
        assert healthy[0].name == "source1"
        assert healthy[1].name == "source3"

    @pytest.mark.asyncio
    async def test_check_with_timeout(self, health_checker):
        """测试超时检查"""
        source = MockDataSource("test", is_healthy=True, timeout=1)

        status = await health_checker.check_source(source)

        assert status.response_time_ms < 1000  # 应该很快完成

    @pytest.mark.asyncio
    async def test_check_with_exception(self, health_checker):
        """测试检查时发生异常"""
        source = MagicMock()
        source.name = "test"
        source.timeout = 10
        source.health_check = AsyncMock(side_effect=Exception("Connection failed"))

        status = await health_checker.check_source(source)

        assert status.is_healthy is False
        assert "Connection failed" in status.error_message
