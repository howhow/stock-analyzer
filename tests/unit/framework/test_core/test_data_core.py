"""测试数据核心模块"""

from datetime import date

import pytest

from framework.core.data_core import DataCore


class TestDataCore:
    """测试 DataCore"""

    def test_init_default(self):
        """测试默认初始化"""
        core = DataCore()

        assert core._plugins == {}
        assert "tushare" in core._priority
        assert core._cache_ttl == 1800

    def test_init_with_plugins(self):
        """测试带插件初始化"""
        from tests.unit.framework.test_interfaces.test_data_source_interface import (
            MockDataSource,
        )

        mock = MockDataSource()
        core = DataCore(plugins={"mock": mock})

        assert "mock" in core._plugins
        assert core._plugins["mock"].name == "mock"

    def test_register_plugin(self):
        """测试注册插件"""
        from tests.unit.framework.test_interfaces.test_data_source_interface import (
            MockDataSource,
        )

        core = DataCore()
        mock = MockDataSource()
        core.register_plugin(mock)

        assert "mock" in core._plugins

    def test_get_available_sources(self):
        """测试获取可用数据源"""
        from tests.unit.framework.test_interfaces.test_data_source_interface import (
            MockDataSource,
        )

        core = DataCore()
        mock = MockDataSource()
        core.register_plugin(mock)

        sources = core.get_available_sources()

        assert "mock" in sources

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        from tests.unit.framework.test_interfaces.test_data_source_interface import (
            MockDataSource,
        )

        core = DataCore()
        mock = MockDataSource()
        core.register_plugin(mock)

        results = await core.health_check()

        assert "mock" in results
        assert results["mock"] is True

    @pytest.mark.asyncio
    async def test_get_quotes_not_implemented(self):
        """测试 get_quotes 数据源未找到"""
        from app.core.exceptions import DataSourceNotFoundError

        core = DataCore()

        with pytest.raises(DataSourceNotFoundError):
            await core.get_quotes(
                "600519.SH",
                date(2024, 1, 1),
                date(2024, 1, 10),
            )
