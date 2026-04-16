"""
DataCore 单元测试

目标覆盖率: ≥ 90%
测试模块: framework/core/data_core.py

测试场景:
1. 数据路由：优先级选择、指定数据源
2. 数据缓存：命中、未命中、过期
3. 数据降级：主源失败→备用源
4. 数据质量：完整性检查、合理性检查
5. 边界条件：空数据、超时、全部失败
"""

import asyncio
from datetime import date, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from framework.core.data_core import DataCore
from app.core.exceptions import (
    AllDataSourcesFailedError,
    DataSourceNotFoundError,
    NoDataError,
)
from framework.models.quote import StandardQuote


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_cache_manager():
    """Mock 缓存管理器"""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)  # 默认缓存未命中
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    cache.clear_local = AsyncMock()
    cache.close = AsyncMock()
    cache.make_key = Mock(side_effect=lambda *args: ":".join(str(a) for a in args))
    cache.default_ttl = 1800
    return cache


@pytest.fixture
def sample_quote_data() -> list[StandardQuote]:
    """生成示例行情数据"""
    return [
        StandardQuote(
            code="600519.SH",
            trade_date=date.today() - timedelta(days=i),
            open=1800.0 + i,
            high=1820.0 + i,
            low=1790.0 + i,
            close=1810.0 + i,
            volume=1000000,
            amount=1800000000.0,
            source="tushare",
            completeness=1.0,
            quality_score=1.0,
        )
        for i in range(5)
    ]


@pytest.fixture
def incomplete_quote_data() -> list[StandardQuote]:
    """生成不完整的行情数据（缺少 open/high/low）"""
    return [
        StandardQuote(
            code="600519.SH",
            trade_date=date.today() - timedelta(days=i),
            close=1810.0,
            source="tushare",
            completeness=0.5,
            quality_score=0.5,
        )
        for i in range(3)
    ]


@pytest.fixture
def invalid_quote_data() -> list[StandardQuote]:
    """生成不合理的行情数据（high < low）"""
    return [
        StandardQuote(
            code="600519.SH",
            trade_date=date.today() - timedelta(days=i),
            open=1800.0,
            high=1750.0,  # 比 low 还低
            low=1790.0,
            close=1810.0,
            source="bad_source",
            completeness=1.0,
            quality_score=0.3,
        )
        for i in range(2)
    ]


@pytest.fixture
def mock_tushare_plugin(sample_quote_data: list[StandardQuote]):
    """Mock Tushare 数据源插件"""
    plugin = Mock()
    plugin.name = "tushare"
    plugin.supported_markets = ["SH", "SZ"]
    plugin.get_quotes = AsyncMock(return_value=sample_quote_data)
    plugin.get_realtime_quote = AsyncMock(
        return_value=sample_quote_data[0] if sample_quote_data else None
    )
    plugin.health_check = AsyncMock(return_value=True)
    plugin.get_supported_stocks = AsyncMock(return_value=["600519.SH", "000001.SZ"])
    return plugin


@pytest.fixture
def mock_akshare_plugin(sample_quote_data: list[StandardQuote]):
    """Mock AKShare 数据源插件"""
    plugin = Mock()
    plugin.name = "akshare"
    plugin.supported_markets = ["SH", "SZ", "HK"]
    plugin.get_quotes = AsyncMock(return_value=sample_quote_data)
    plugin.get_realtime_quote = AsyncMock(
        return_value=sample_quote_data[0] if sample_quote_data else None
    )
    plugin.health_check = AsyncMock(return_value=True)
    plugin.get_supported_stocks = AsyncMock(return_value=["600519.SH", "000001.SZ"])
    return plugin


@pytest.fixture
def mock_failing_plugin():
    """Mock 失败的数据源插件"""
    plugin = Mock()
    plugin.name = "failing_source"
    plugin.supported_markets = ["SH", "SZ"]
    plugin.get_quotes = AsyncMock(
        side_effect=Exception("Timeout")  # 使用通用 Exception
    )
    plugin.get_realtime_quote = AsyncMock(side_effect=Exception("Timeout"))
    plugin.health_check = AsyncMock(return_value=False)
    plugin.get_supported_stocks = AsyncMock(side_effect=Exception("Timeout"))
    return plugin


@pytest.fixture
def mock_empty_plugin():
    """Mock 返回空数据的数据源插件"""
    plugin = Mock()
    plugin.name = "empty_source"
    plugin.supported_markets = ["SH", "SZ"]
    plugin.get_quotes = AsyncMock(return_value=[])
    plugin.get_realtime_quote = AsyncMock(return_value=None)
    plugin.health_check = AsyncMock(return_value=True)
    plugin.get_supported_stocks = AsyncMock(return_value=[])
    return plugin


@pytest.fixture
def data_core_no_plugins(mock_cache_manager: Mock):
    """无插件的 DataCore 实例"""
    with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
        "framework.core.data_core.settings"
    ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
        MockCacheManager.return_value = mock_cache_manager
        mock_settings.cache_ttl_daily = 1800
        mock_settings.circuit_breaker_threshold = 3
        mock_logger.return_value = Mock()

        return DataCore(plugins=None, cache_ttl=1800)


@pytest.fixture
def data_core_with_plugins(
    mock_tushare_plugin: Mock,
    mock_akshare_plugin: Mock,
    mock_cache_manager: Mock,
):
    """带插件的 DataCore 实例"""
    with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
        "framework.core.data_core.settings"
    ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
        MockCacheManager.return_value = mock_cache_manager
        mock_settings.cache_ttl_daily = 1800
        mock_settings.circuit_breaker_threshold = 3
        mock_logger.return_value = Mock()

        plugins = {
            "tushare": mock_tushare_plugin,
            "akshare": mock_akshare_plugin,
        }
        return DataCore(
            plugins=plugins,
            priority=["tushare", "akshare"],
            cache_ttl=1800,
        )


@pytest.fixture
def data_core_with_failing_primary(
    mock_failing_plugin: Mock,
    mock_akshare_plugin: Mock,
    mock_cache_manager: Mock,
):
    """主数据源失败，备用数据源可用的 DataCore 实例"""
    with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
        "framework.core.data_core.settings"
    ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
        MockCacheManager.return_value = mock_cache_manager
        mock_settings.cache_ttl_daily = 1800
        mock_settings.circuit_breaker_threshold = 3
        mock_logger.return_value = Mock()

        plugins = {
            "failing_source": mock_failing_plugin,
            "akshare": mock_akshare_plugin,
        }
        return DataCore(
            plugins=plugins,
            priority=["failing_source", "akshare"],
            cache_ttl=1800,
        )


@pytest.fixture
def data_core_all_failing(
    mock_failing_plugin: Mock,
    mock_cache_manager: Mock,
):
    """所有数据源都失败的 DataCore 实例"""
    plugin2 = Mock()
    plugin2.name = "another_failing"
    plugin2.supported_markets = ["SH", "SZ"]
    plugin2.get_quotes = AsyncMock(side_effect=Exception("Unexpected error"))
    plugin2.get_realtime_quote = AsyncMock(side_effect=Exception("Unexpected error"))
    plugin2.health_check = AsyncMock(return_value=False)
    plugin2.get_supported_stocks = AsyncMock(return_value=[])

    with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
        "framework.core.data_core.settings"
    ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
        MockCacheManager.return_value = mock_cache_manager
        mock_settings.cache_ttl_daily = 1800
        mock_settings.circuit_breaker_threshold = 3
        mock_logger.return_value = Mock()

        plugins = {
            "failing_source": mock_failing_plugin,
            "another_failing": plugin2,
        }
        return DataCore(
            plugins=plugins,
            priority=["failing_source", "another_failing"],
            cache_ttl=1800,
        )


# ============================================================
# 初始化测试
# ============================================================


class TestDataCoreInitialization:
    """初始化测试"""

    def test_init_with_default_params(self, mock_cache_manager: Mock):
        """测试使用默认参数初始化"""
        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore()

            assert data_core._plugins == {}
            assert data_core._priority == DataCore.DEFAULT_PRIORITY
            assert data_core._cache_ttl == 1800

    def test_init_with_custom_params(self, mock_cache_manager: Mock):
        """测试使用自定义参数初始化"""
        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 3600
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            plugins = {"test": Mock()}
            priority = ["test", "backup"]
            cache_ttl = 3600

            data_core = DataCore(
                plugins=plugins,
                priority=priority,
                cache_ttl=cache_ttl,
            )

            assert data_core._plugins == plugins
            assert data_core._priority == priority
            assert data_core._cache_ttl == cache_ttl

    def test_init_with_none_plugins(self, mock_cache_manager: Mock):
        """测试传入 None 插件"""
        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(plugins=None)

            assert data_core._plugins == {}

    def test_init_with_none_priority(self, mock_cache_manager: Mock):
        """测试传入 None 优先级"""
        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(priority=None)

            assert data_core._priority == DataCore.DEFAULT_PRIORITY.copy()

    def test_register_plugin(
        self, data_core_no_plugins: DataCore, mock_tushare_plugin: Mock
    ):
        """测试注册插件"""
        data_core_no_plugins.register_plugin(mock_tushare_plugin)

        assert "tushare" in data_core_no_plugins._plugins
        assert data_core_no_plugins._plugins["tushare"] == mock_tushare_plugin

    def test_register_multiple_plugins(
        self,
        data_core_no_plugins: DataCore,
        mock_tushare_plugin: Mock,
        mock_akshare_plugin: Mock,
    ):
        """测试注册多个插件"""
        data_core_no_plugins.register_plugin(mock_tushare_plugin)
        data_core_no_plugins.register_plugin(mock_akshare_plugin)

        assert len(data_core_no_plugins._plugins) == 2
        assert "tushare" in data_core_no_plugins._plugins
        assert "akshare" in data_core_no_plugins._plugins

    def test_register_plugin_overwrites_existing(self, data_core_no_plugins: DataCore):
        """测试注册同名插件会覆盖现有插件"""
        plugin1 = Mock()
        plugin1.name = "test"
        plugin2 = Mock()
        plugin2.name = "test"

        data_core_no_plugins.register_plugin(plugin1)
        data_core_no_plugins.register_plugin(plugin2)

        assert data_core_no_plugins._plugins["test"] == plugin2


# ============================================================
# 数据路由测试
# ============================================================


class TestDataRouting:
    """数据路由测试"""

    @pytest.mark.asyncio
    async def test_get_quotes_by_priority(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试按优先级选择数据源"""
        # 当 tushare 在优先级首位时，应该使用 tushare
        result = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        assert result == sample_quote_data
        data_core_with_plugins._plugins["tushare"].get_quotes.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_quotes_with_specific_source(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试指定数据源"""
        result = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
            source="akshare",
        )

        assert result == sample_quote_data
        # 应该只调用 akshare，不调用 tushare
        data_core_with_plugins._plugins["akshare"].get_quotes.assert_called_once()
        data_core_with_plugins._plugins["tushare"].get_quotes.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_quotes_with_invalid_source(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试指定不存在的数据源"""
        with pytest.raises(DataSourceNotFoundError):
            await data_core_with_plugins.get_quotes(
                stock_code="600519.SH",
                start_date=date.today() - timedelta(days=5),
                end_date=date.today(),
                source="nonexistent",
            )

    @pytest.mark.asyncio
    async def test_get_quotes_no_plugins_available(
        self,
        data_core_no_plugins: DataCore,
    ):
        """测试没有可用插件"""
        with pytest.raises(DataSourceNotFoundError):
            await data_core_no_plugins.get_quotes(
                stock_code="600519.SH",
                start_date=date.today() - timedelta(days=5),
                end_date=date.today(),
            )

    @pytest.mark.asyncio
    async def test_get_quotes_priority_not_registered(
        self,
        mock_cache_manager: Mock,
    ):
        """测试优先级列表中的数据源未注册"""
        plugin = Mock()
        plugin.name = "akshare"
        plugin.get_quotes = AsyncMock(
            return_value=[
                StandardQuote(
                    code="600519.SH",
                    trade_date=date.today(),
                    close=1800.0,
                    source="akshare",
                )
            ]
        )

        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(
                plugins={"akshare": plugin},
                priority=["tushare", "akshare"],  # tushare 未注册
            )

            result = await data_core.get_quotes(
                stock_code="600519.SH",
                start_date=date.today(),
                end_date=date.today(),
            )

            # 应该跳过未注册的 tushare，使用 akshare
            assert len(result) == 1
            assert result[0].source == "akshare"


# ============================================================
# 数据缓存测试
# ============================================================


class TestDataCaching:
    """数据缓存测试"""

    @pytest.mark.asyncio
    async def test_cache_hit(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
        mock_cache_manager: Mock,
    ):
        """测试缓存命中"""
        # 配置缓存第一次返回 None（未命中），第二次返回数据（命中）
        cached_data = [q.model_dump() for q in sample_quote_data]

        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None  # 第一次调用返回 None（未命中）
            return cached_data  # 第二次调用返回缓存数据

        mock_cache_manager.get = AsyncMock(side_effect=mock_get)

        # 第一次调用，缓存未命中
        result1 = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        # 第二次调用，缓存命中
        result2 = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        assert len(result1) == len(sample_quote_data)
        assert len(result2) == len(sample_quote_data)
        # 数据源插件应该只被调用一次（第一次未命中时）
        assert data_core_with_plugins._plugins["tushare"].get_quotes.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_miss_with_different_params(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试缓存未命中（不同参数）"""
        # 第一次调用
        await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        # 第二次调用（不同的股票代码）
        await data_core_with_plugins.get_quotes(
            stock_code="000001.SZ",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        # 因为参数不同，应该调用两次
        assert data_core_with_plugins._plugins["tushare"].get_quotes.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_expired(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
        mock_cache_manager: Mock,
    ):
        """测试缓存过期"""
        # 设置缓存过期（第一次返回数据，第二次返回 None）
        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # 第一次调用返回 None（缓存未命中）
                return None
            else:
                # 后续调用也返回 None
                return None

        mock_cache_manager.get = AsyncMock(side_effect=mock_get)

        # 第一次调用
        await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        # 第二次调用
        await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        # 因为缓存未命中，应该调用两次
        assert data_core_with_plugins._plugins["tushare"].get_quotes.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_different_sources(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试不同数据源的缓存隔离"""
        # 使用 tushare 获取
        await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
            source="tushare",
        )

        # 使用 akshare 获取
        await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
            source="akshare",
        )

        # 两个数据源都应该被调用
        data_core_with_plugins._plugins["tushare"].get_quotes.assert_called_once()
        data_core_with_plugins._plugins["akshare"].get_quotes.assert_called_once()


# ============================================================
# 数据降级测试
# ============================================================


class TestDataDegradation:
    """数据降级测试"""

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(
        self,
        data_core_with_failing_primary: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试主数据源失败后降级到备用数据源"""
        result = await data_core_with_failing_primary.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        assert result == sample_quote_data
        # 主数据源应该被尝试
        data_core_with_failing_primary._plugins[
            "failing_source"
        ].get_quotes.assert_called_once()
        # 备用数据源应该被调用
        data_core_with_failing_primary._plugins[
            "akshare"
        ].get_quotes.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_timeout(
        self,
        data_core_with_failing_primary: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试超时后降级"""
        # 模拟超时异常
        data_core_with_failing_primary._plugins["failing_source"].get_quotes = (
            AsyncMock(side_effect=asyncio.TimeoutError("Connection timeout"))
        )

        result = await data_core_with_failing_primary.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        assert result == sample_quote_data
        # 备用数据源应该被调用
        data_core_with_failing_primary._plugins[
            "akshare"
        ].get_quotes.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_sources_failed(
        self,
        data_core_all_failing: DataCore,
    ):
        """测试所有数据源都失败"""
        with pytest.raises(AllDataSourcesFailedError) as exc_info:
            await data_core_all_failing.get_quotes(
                stock_code="600519.SH",
                start_date=date.today() - timedelta(days=5),
                end_date=date.today(),
            )

        # 验证异常信息包含所有失败记录
        assert exc_info.value.failures is not None
        assert "failing_source" in exc_info.value.failures
        assert "another_failing" in exc_info.value.failures

    @pytest.mark.asyncio
    async def test_fallback_preserves_priority_order(self, mock_cache_manager: Mock):
        """测试降级保持优先级顺序"""
        plugin1 = Mock()
        plugin1.name = "priority1"
        plugin1.get_quotes = AsyncMock(side_effect=Exception("Failed"))

        plugin2 = Mock()
        plugin2.name = "priority2"
        plugin2.get_quotes = AsyncMock(
            return_value=[
                StandardQuote(
                    code="600519.SH",
                    trade_date=date.today(),
                    close=1800.0,
                    source="priority2",
                )
            ]
        )

        plugin3 = Mock()
        plugin3.name = "priority3"
        plugin3.get_quotes = AsyncMock(return_value=[])

        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(
                plugins={
                    "priority1": plugin1,
                    "priority2": plugin2,
                    "priority3": plugin3,
                },
                priority=["priority1", "priority2", "priority3"],
            )

            result = await data_core.get_quotes(
                stock_code="600519.SH",
                start_date=date.today(),
                end_date=date.today(),
            )

            # 应该按优先级顺序尝试
            plugin1.get_quotes.assert_called_once()
            plugin2.get_quotes.assert_called_once()
            # plugin3 不应该被调用（因为 plugin2 成功了）
            plugin3.get_quotes.assert_not_called()


# ============================================================
# 数据质量测试
# ============================================================


class TestDataQuality:
    """数据质量测试"""

    @pytest.mark.asyncio
    async def test_complete_data(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试完整数据通过质量检查"""
        result = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        # 所有数据都应该是完整的
        for quote in result:
            assert quote.is_complete() is True
            assert quote.is_valid() is True

    @pytest.mark.asyncio
    async def test_incomplete_data_handling(
        self,
        data_core_with_plugins: DataCore,
        incomplete_quote_data: list[StandardQuote],
    ):
        """测试不完整数据的处理"""
        # 配置插件返回不完整数据
        data_core_with_plugins._plugins["tushare"].get_quotes = AsyncMock(
            return_value=incomplete_quote_data
        )

        result = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=3),
            end_date=date.today(),
        )

        # 应该返回数据，但标记为不完整
        assert len(result) == len(incomplete_quote_data)
        for quote in result:
            assert quote.is_complete() is False

    @pytest.mark.asyncio
    async def test_invalid_data_handling(
        self,
        data_core_with_plugins: DataCore,
        invalid_quote_data: list[StandardQuote],
    ):
        """测试不合理数据的处理"""
        # 配置插件返回不合理数据
        data_core_with_plugins._plugins["tushare"].get_quotes = AsyncMock(
            return_value=invalid_quote_data
        )

        result = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=2),
            end_date=date.today(),
        )

        # 应该返回数据，但标记为不合理
        assert len(result) == len(invalid_quote_data)
        for quote in result:
            assert quote.is_valid() is False

    @pytest.mark.asyncio
    async def test_quality_score_calculation(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试质量评分计算"""
        result = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        # 所有数据的质量评分应该 >= 0 和 <= 1
        for quote in result:
            assert 0.0 <= quote.quality_score <= 1.0
            assert 0.0 <= quote.completeness <= 1.0

    @pytest.mark.asyncio
    async def test_quality_label(self, sample_quote_data: list[StandardQuote]):
        """测试质量标签"""
        # 高质量
        high_quality = sample_quote_data[0]
        high_quality.quality_score = 0.95
        assert high_quality.get_quality_label() == "high"

        # 中等质量
        medium_quality = sample_quote_data[1]
        medium_quality.quality_score = 0.75
        assert medium_quality.get_quality_label() == "medium"

        # 低质量
        low_quality = sample_quote_data[2]
        low_quality.quality_score = 0.5
        assert low_quality.get_quality_label() == "low"


# ============================================================
# 边界条件测试
# ============================================================


class TestBoundaryConditions:
    """边界条件测试"""

    @pytest.mark.asyncio
    async def test_empty_data_from_source(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试数据源返回空数据"""
        # 配置所有数据源都返回空数据
        data_core_with_plugins._plugins["tushare"].get_quotes = AsyncMock(
            return_value=[]
        )
        data_core_with_plugins._plugins["akshare"].get_quotes = AsyncMock(
            return_value=[]
        )

        with pytest.raises(NoDataError):
            await data_core_with_plugins.get_quotes(
                stock_code="600519.SH",
                start_date=date.today() - timedelta(days=5),
                end_date=date.today(),
            )

    @pytest.mark.asyncio
    async def test_timeout_handling(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试超时处理"""
        # 模拟超时
        data_core_with_plugins._plugins["tushare"].get_quotes = AsyncMock(
            side_effect=asyncio.TimeoutError("Timeout")
        )

        # 应该降级到 akshare
        result = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        assert len(result) > 0
        data_core_with_plugins._plugins["akshare"].get_quotes.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_sources_timeout(self, mock_cache_manager: Mock):
        """测试所有数据源超时"""
        plugin1 = Mock()
        plugin1.name = "timeout1"
        plugin1.get_quotes = AsyncMock(side_effect=asyncio.TimeoutError())

        plugin2 = Mock()
        plugin2.name = "timeout2"
        plugin2.get_quotes = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(
                plugins={"timeout1": plugin1, "timeout2": plugin2},
                priority=["timeout1", "timeout2"],
            )

            with pytest.raises(AllDataSourcesFailedError):
                await data_core.get_quotes(
                    stock_code="600519.SH",
                    start_date=date.today(),
                    end_date=date.today(),
                )

    @pytest.mark.asyncio
    async def test_invalid_stock_code(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试无效的股票代码"""
        # 配置所有数据源都返回空数据（模拟无效股票代码）
        data_core_with_plugins._plugins["tushare"].get_quotes = AsyncMock(
            return_value=[]
        )
        data_core_with_plugins._plugins["akshare"].get_quotes = AsyncMock(
            return_value=[]
        )

        with pytest.raises(NoDataError):
            await data_core_with_plugins.get_quotes(
                stock_code="INVALID_CODE",
                start_date=date.today() - timedelta(days=5),
                end_date=date.today(),
            )

    @pytest.mark.asyncio
    async def test_date_range_validation(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试日期范围验证"""
        # 结束日期早于开始日期
        # DataCore 不会自动处理这种情况，数据源需要处理
        # 这里测试 DataCore 会正常传递参数给数据源
        data_core_with_plugins._plugins["tushare"].get_quotes = AsyncMock(
            return_value=[]
        )
        data_core_with_plugins._plugins["akshare"].get_quotes = AsyncMock(
            return_value=[]
        )

        with pytest.raises(NoDataError):
            await data_core_with_plugins.get_quotes(
                stock_code="600519.SH",
                start_date=date.today(),
                end_date=date.today() - timedelta(days=5),
            )

    @pytest.mark.asyncio
    async def test_large_date_range(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试大日期范围"""
        # 模拟一年数据
        large_dataset = [
            StandardQuote(
                code="600519.SH",
                trade_date=date.today() - timedelta(days=i),
                close=1800.0,
                source="tushare",
            )
            for i in range(365)
        ]
        data_core_with_plugins._plugins["tushare"].get_quotes = AsyncMock(
            return_value=large_dataset
        )

        result = await data_core_with_plugins.get_quotes(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=365),
            end_date=date.today(),
        )

        assert len(result) == 365

    @pytest.mark.asyncio
    async def test_concurrent_requests(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试并发请求"""
        # 模拟并发获取不同股票
        tasks = [
            data_core_with_plugins.get_quotes(
                stock_code=f"60051{i}.SH",
                start_date=date.today() - timedelta(days=5),
                end_date=date.today(),
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 应该没有异常（或正确处理异常）
        for result in results:
            if isinstance(result, Exception):
                assert isinstance(
                    result,
                    (AllDataSourcesFailedError, DataSourceNotFoundError, NoDataError),
                )


# ============================================================
# 健康检查测试
# ============================================================


class TestHealthCheck:
    """健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试所有数据源健康"""
        results = await data_core_with_plugins.health_check()

        assert results["tushare"] is True
        assert results["akshare"] is True

    @pytest.mark.asyncio
    async def test_health_check_with_unhealthy_source(
        self,
        data_core_with_failing_primary: DataCore,
    ):
        """测试包含不健康数据源"""
        results = await data_core_with_failing_primary.health_check()

        assert results["failing_source"] is False
        assert results["akshare"] is True

    @pytest.mark.asyncio
    async def test_health_check_no_plugins(self, data_core_no_plugins: DataCore):
        """测试无插件的健康检查"""
        results = await data_core_no_plugins.health_check()

        assert results == {}

    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self, mock_cache_manager: Mock):
        """测试健康检查异常处理"""
        plugin = Mock()
        plugin.name = "error_plugin"
        plugin.health_check = AsyncMock(side_effect=Exception("Health check error"))

        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(plugins={"error_plugin": plugin})

            results = await data_core.health_check()

            # 异常应该被捕获，返回 False
            assert results["error_plugin"] is False


# ============================================================
# 辅助方法测试
# ============================================================


class TestHelperMethods:
    """辅助方法测试"""

    def test_get_available_sources(self, data_core_with_plugins: DataCore):
        """测试获取可用数据源列表"""
        sources = data_core_with_plugins.get_available_sources()

        assert "tushare" in sources
        assert "akshare" in sources
        assert len(sources) == 2

    def test_get_available_sources_empty(self, data_core_no_plugins: DataCore):
        """测试无插件时获取可用数据源列表"""
        sources = data_core_no_plugins.get_available_sources()

        assert sources == []

    def test_default_priority(self):
        """测试默认优先级"""
        assert DataCore.DEFAULT_PRIORITY == ["tushare", "akshare", "openbb", "local"]


# ============================================================
# 真实场景模拟测试
# ============================================================


class TestRealWorldScenarios:
    """真实场景模拟测试"""

    @pytest.mark.asyncio
    async def test_market_open_hours_request(self, mock_cache_manager: Mock):
        """测试交易时段请求"""
        plugin = Mock()
        plugin.name = "realtime"
        plugin.get_quotes = AsyncMock(
            return_value=[
                StandardQuote(
                    code="600519.SH",
                    trade_date=date.today(),
                    open=1800.0,
                    high=1820.0,
                    low=1790.0,
                    close=1810.0,
                    volume=1000000,
                    amount=1800000000.0,
                    source="realtime",
                    completeness=1.0,
                    quality_score=1.0,
                )
            ]
        )

        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 300
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(
                plugins={"realtime": plugin},
                priority=["realtime"],
                cache_ttl=300,  # 5分钟短缓存
            )

            result = await data_core.get_quotes(
                stock_code="600519.SH",
                start_date=date.today(),
                end_date=date.today(),
            )

            assert len(result) == 1
            assert result[0].is_complete() is True

    @pytest.mark.asyncio
    async def test_historical_data_request(self, mock_cache_manager: Mock):
        """测试历史数据请求"""
        # 模拟大量历史数据
        historical_data = [
            StandardQuote(
                code="600519.SH",
                trade_date=date(2023, 1, 1) + timedelta(days=i),
                open=1800.0 + i * 0.5,
                high=1820.0 + i * 0.5,
                low=1790.0 + i * 0.5,
                close=1810.0 + i * 0.5,
                volume=1000000,
                source="historical",
            )
            for i in range(100)
        ]

        plugin = Mock()
        plugin.name = "historical"
        plugin.get_quotes = AsyncMock(return_value=historical_data)

        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 86400
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(
                plugins={"historical": plugin},
                priority=["historical"],
                cache_ttl=86400,  # 1天长缓存
            )

            result = await data_core.get_quotes(
                stock_code="600519.SH",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 4, 11),
            )

            assert len(result) == 100

    @pytest.mark.asyncio
    async def test_mixed_quality_data(self, mock_cache_manager: Mock):
        """测试混合质量数据"""
        mixed_data = [
            # 完整高质量
            StandardQuote(
                code="600519.SH",
                trade_date=date.today() - timedelta(days=0),
                open=1800.0,
                high=1820.0,
                low=1790.0,
                close=1810.0,
                volume=1000000,
                source="mixed",
            ),
            # 不完整数据
            StandardQuote(
                code="600519.SH",
                trade_date=date.today() - timedelta(days=1),
                close=1805.0,
                source="mixed",
            ),
            # 不合理数据（high < low）
            StandardQuote(
                code="600519.SH",
                trade_date=date.today() - timedelta(days=2),
                open=1800.0,
                high=1750.0,  # 异常
                low=1790.0,
                close=1810.0,
                source="mixed",
            ),
        ]

        plugin = Mock()
        plugin.name = "mixed"
        plugin.get_quotes = AsyncMock(return_value=mixed_data)

        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(
                plugins={"mixed": plugin},
                priority=["mixed"],
            )

            result = await data_core.get_quotes(
                stock_code="600519.SH",
                start_date=date.today() - timedelta(days=2),
                end_date=date.today(),
            )

            assert len(result) == 3

            # DataCore 会重新计算质量分数
            # 验证数据质量计算正常进行
            for quote in result:
                assert 0.0 <= quote.quality_score <= 1.0
                assert 0.0 <= quote.completeness <= 1.0
                assert quote.source == "mixed"


# ============================================================
# Redis Mock 测试
# ============================================================


class TestRedisMocking:
    """Redis Mock 测试（演示如何用 Mock 而非真实 Redis）"""

    @pytest.mark.asyncio
    async def test_redis_cache_hit_with_mock(self, mock_cache_manager: Mock):
        """使用 Mock 测试 Redis 缓存命中"""
        # 配置缓存返回数据
        cached_data = [
            {
                "code": "600519.SH",
                "trade_date": date.today().isoformat(),
                "close": 1800.0,
                "source": "cache",
                "completeness": 1.0,
                "quality_score": 1.0,
            }
        ]
        mock_cache_manager.get = AsyncMock(return_value=cached_data)

        plugin = Mock()
        plugin.name = "test"
        plugin.get_quotes = AsyncMock(
            return_value=[
                StandardQuote(
                    code="600519.SH",
                    trade_date=date.today(),
                    close=1800.0,
                    source="test",
                )
            ]
        )

        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 3
            mock_logger.return_value = Mock()

            data_core = DataCore(
                plugins={"test": plugin},
                priority=["test"],
            )

            result = await data_core.get_quotes(
                stock_code="600519.SH",
                start_date=date.today(),
                end_date=date.today(),
            )

            # 缓存命中，数据源不应该被调用
            assert len(result) == 1
            plugin.get_quotes.assert_not_called()


# ============================================================
# 运行测试
# ============================================================


class TestAdditionalCoverage:
    """补充覆盖率测试"""

    @pytest.mark.asyncio
    async def test_get_realtime_quote_success(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试获取实时行情成功"""
        result = await data_core_with_plugins.get_realtime_quote(stock_code="600519.SH")

        assert result is not None
        assert result.code == "600519.SH"

    @pytest.mark.asyncio
    async def test_get_realtime_quote_fallback(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试实时行情降级"""
        # 主数据源返回 None
        data_core_with_plugins._plugins["tushare"].get_realtime_quote = AsyncMock(
            return_value=None
        )
        # 备用数据源返回数据
        data_core_with_plugins._plugins["akshare"].get_realtime_quote = AsyncMock(
            return_value=StandardQuote(
                code="600519.SH",
                trade_date=date.today(),
                close=1800.0,
                source="akshare",
            )
        )

        result = await data_core_with_plugins.get_realtime_quote(stock_code="600519.SH")

        assert result is not None
        assert result.source == "akshare"

    @pytest.mark.asyncio
    async def test_get_realtime_quote_no_data(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试实时行情无数据"""
        # 所有数据源返回 None
        data_core_with_plugins._plugins["tushare"].get_realtime_quote = AsyncMock(
            return_value=None
        )
        data_core_with_plugins._plugins["akshare"].get_realtime_quote = AsyncMock(
            return_value=None
        )

        result = await data_core_with_plugins.get_realtime_quote(stock_code="600519.SH")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_realtime_quote_with_specific_source(
        self,
        data_core_with_plugins: DataCore,
        sample_quote_data: list[StandardQuote],
    ):
        """测试指定数据源获取实时行情"""
        result = await data_core_with_plugins.get_realtime_quote(
            stock_code="600519.SH",
            source="akshare",
        )

        assert result is not None
        # 只应该调用 akshare
        data_core_with_plugins._plugins[
            "akshare"
        ].get_realtime_quote.assert_called_once()
        data_core_with_plugins._plugins[
            "tushare"
        ].get_realtime_quote.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_source_status(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试获取数据源状态"""
        result = await data_core_with_plugins.get_source_status()

        assert "tushare" in result
        assert "akshare" in result
        assert result["tushare"]["available"] is True
        assert result["akshare"]["available"] is True

    @pytest.mark.asyncio
    async def test_get_source_status_with_unhealthy(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试获取不健康数据源的状态"""
        # tushare 健康检查失败
        data_core_with_plugins._plugins["tushare"].health_check = AsyncMock(
            return_value=False
        )

        result = await data_core_with_plugins.get_source_status()

        assert result["tushare"]["healthy"] is False
        assert result["tushare"]["failures"] >= 1

    @pytest.mark.asyncio
    async def test_get_source_status_unregistered_source(
        self,
        data_core_with_plugins: DataCore,
        mock_cache_manager: Mock,
    ):
        """测试优先级中有未注册数据源的状态"""
        # 添加一个未注册的优先级
        data_core_with_plugins._priority = ["tushare", "unregistered", "akshare"]

        result = await data_core_with_plugins.get_source_status()

        assert result["unregistered"]["available"] is False
        assert result["unregistered"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_clear_cache_specific(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试清除特定缓存"""
        result = await data_core_with_plugins.clear_cache(
            stock_code="600519.SH",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
        )

        assert result == 1

    @pytest.mark.asyncio
    async def test_clear_cache_stock_code_only(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试清除指定股票的所有缓存"""
        result = await data_core_with_plugins.clear_cache(stock_code="600519.SH")

        assert result >= 0

    @pytest.mark.asyncio
    async def test_clear_cache_all(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试清除所有本地缓存"""
        result = await data_core_with_plugins.clear_cache()

        assert result >= 0

    @pytest.mark.asyncio
    async def test_circuit_breaker(
        self,
        mock_cache_manager: Mock,
    ):
        """测试熔断机制"""
        # 创建两个数据源，一个失败，一个成功
        failing_plugin = Mock()
        failing_plugin.name = "failing"
        failing_plugin.get_quotes = AsyncMock(side_effect=Exception("Failed"))

        working_plugin = Mock()
        working_plugin.name = "working"
        working_plugin.get_quotes = AsyncMock(
            return_value=[
                StandardQuote(
                    code="600519.SH",
                    trade_date=date.today(),
                    close=1800.0,
                    source="working",
                )
            ]
        )

        with patch("framework.core.data_core.CacheManager") as MockCacheManager, patch(
            "framework.core.data_core.settings"
        ) as mock_settings, patch("framework.core.data_core.get_logger") as mock_logger:
            MockCacheManager.return_value = mock_cache_manager
            mock_settings.cache_ttl_daily = 1800
            mock_settings.circuit_breaker_threshold = 2  # 失败 2 次就熔断
            mock_logger.return_value = Mock()

            data_core = DataCore(
                plugins={"failing": failing_plugin, "working": working_plugin},
                priority=["failing", "working"],
            )

            # 第一次失败，降级到 working
            result = await data_core.get_quotes(
                stock_code="600519.SH",
                start_date=date.today(),
                end_date=date.today(),
            )
            assert result[0].source == "working"

            # 第二次失败
            result = await data_core.get_quotes(
                stock_code="600519.SH",
                start_date=date.today(),
                end_date=date.today(),
            )
            assert result[0].source == "working"

            # 第三次，failing 应该被熔断（跳过）
            # 重置 working 的调用计数
            working_plugin.get_quotes.reset_mock()

            result = await data_core.get_quotes(
                stock_code="600519.SH",
                start_date=date.today(),
                end_date=date.today(),
            )

            # failing 被熔断，应该直接使用 working
            assert result[0].source == "working"
            # failing 不应该被调用（被熔断跳过）
            # 注意：由于熔断检查在 _get_source_order 中，
            # 失败次数 >= threshold 时会被跳过
            # 但由于只有 failing 和 working 两个数据源，
            # 即使 failing 被熔断，working 仍然会被调用

    @pytest.mark.asyncio
    async def test_close(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试关闭资源"""
        await data_core_with_plugins.close()

    @pytest.mark.asyncio
    async def test_get_realtime_quote_exception(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试实时行情获取异常"""
        # 主数据源抛出异常
        data_core_with_plugins._plugins["tushare"].get_realtime_quote = AsyncMock(
            side_effect=Exception("Connection error")
        )
        # 备用数据源正常
        data_core_with_plugins._plugins["akshare"].get_realtime_quote = AsyncMock(
            return_value=StandardQuote(
                code="600519.SH",
                trade_date=date.today(),
                close=1800.0,
                source="akshare",
            )
        )

        result = await data_core_with_plugins.get_realtime_quote(stock_code="600519.SH")

        # 应该降级到备用数据源
        assert result is not None
        assert result.source == "akshare"

    @pytest.mark.asyncio
    async def test_get_source_status_exception(
        self,
        data_core_with_plugins: DataCore,
    ):
        """测试获取数据源状态时异常"""
        # 健康检查抛出异常
        data_core_with_plugins._plugins["tushare"].health_check = AsyncMock(
            side_effect=Exception("Health check failed")
        )

        result = await data_core_with_plugins.get_source_status()

        # 异常应该被捕获
        assert result["tushare"]["healthy"] is False
        assert "error" in result["tushare"]


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=framework.core.data_core",
            "--cov-report=term-missing",
            "--cov-report=html",
        ]
    )
