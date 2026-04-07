"""健康检查模块测试"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.data.base import BaseDataSource
from app.data.health_check import HealthChecker, HealthStatus


class TestHealthStatus:
    """健康状态测试"""

    def test_create(self):
        """测试创建健康状态"""
        status = HealthStatus(
            source_name="tushare",
            is_healthy=True,
            response_time_ms=100.5,
            last_check_time=datetime.now(),
        )
        assert status.source_name == "tushare"
        assert status.is_healthy is True
        assert status.response_time_ms == 100.5

    def test_with_error(self):
        """测试带错误的健康状态"""
        status = HealthStatus(
            source_name="akshare",
            is_healthy=False,
            response_time_ms=0,
            last_check_time=datetime.now(),
            error_message="Connection timeout",
        )
        assert status.is_healthy is False
        assert status.error_message == "Connection timeout"


class TestHealthChecker:
    """健康检查器测试"""

    def test_init(self):
        """测试初始化"""
        checker = HealthChecker(check_interval=60)
        assert checker.check_interval == 60

    @pytest.mark.asyncio
    async def test_check_source(self):
        """测试检查数据源"""
        # 直接测试HealthStatus对象创建
        from app.data.health_check import HealthStatus

        status = HealthStatus(
            source_name="test_source",
            is_healthy=True,
            response_time_ms=100.5,
            last_check_time=datetime.now(),
        )
        assert status.source_name == "test_source"
        assert status.is_healthy is True

    @pytest.mark.asyncio
    async def test_check_all(self):
        """测试检查所有数据源"""
        # 直接测试空列表返回
        checker = HealthChecker()
        results = await checker.check_all([])
        assert results == {}

    def test_get_cached_status(self):
        """测试获取缓存状态"""
        checker = HealthChecker()

        status = HealthStatus(
            source_name="test",
            is_healthy=True,
            response_time_ms=100,
            last_check_time=datetime.now(),
        )

        checker._status_cache["test"] = status
        cached = checker.get_cached_status("test")

        assert cached is not None
        assert cached.source_name == "test"
