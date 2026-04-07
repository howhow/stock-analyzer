"""
数据获取协调器完整测试

目标覆盖率: ≥ 95%
当前覆盖率: 64%
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from tests.fixtures.mock_data import (
    MOCK_STOCK_INFO_DICT,
    MOCK_DAILY_QUOTES_DICT,
    create_stock_info_dict,
    create_daily_quote_dict,
)

from app.data.base import DataSourceError
from app.data.data_fetcher import DataFetcher
from app.data.health_check import HealthStatus
from app.models.stock import DailyQuote, FinancialData, IntradayQuote, StockInfo


class TestDataFetcherInit:
    """数据获取器初始化测试"""

    def test_init_default(self):
        """测试默认初始化"""
        fetcher = DataFetcher()

        assert fetcher.tushare is not None
        assert fetcher.akshare is not None
        assert fetcher.cache is not None
        assert fetcher.health_checker is not None
        assert len(fetcher.sources) == 2

    def test_init_with_custom_clients(self):
        """测试自定义客户端初始化"""
        mock_tushare = Mock()
        mock_akshare = Mock()
        mock_cache = Mock()

        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        assert fetcher.tushare is mock_tushare
        assert fetcher.akshare is mock_akshare
        assert fetcher.cache is mock_cache


class TestGetStockInfo:
    """获取股票信息测试"""

    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()

    @pytest.mark.asyncio
    async def test_get_stock_info_from_cache(self, fetcher):
        """测试从缓存获取股票信息"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(
            return_value={
                "code": "000001.SZ",
                "name": "平安银行",
            "market": "SZ",
                "industry": "银行",
                            }
        )
        mock_cache.make_key = Mock(return_value="test_key")
        fetcher.cache = mock_cache

        result = await fetcher.get_stock_info("000001.SZ")

        assert result.code == "000001.SZ"
        assert result.name == "平安银行"
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stock_info_from_source(self, fetcher):
        """测试从数据源获取股票信息"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_stock_info = AsyncMock(
            return_value=StockInfo(
                    code="000001.SZ",
                    name="平安银行",
                    market="SZ",
                    industry="银行",
                    list_date=None,
                )
        )

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]

        result = await fetcher.get_stock_info("000001.SZ")

        assert result.code == "000001.SZ"
        mock_source.get_stock_info.assert_called_once()
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stock_info_fallback(self, fetcher):
        """测试数据源降级"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

        mock_source1 = AsyncMock()
        mock_source1.name = "source1"
        mock_source1.get_stock_info = AsyncMock(side_effect=Exception("Failed"))

        mock_source2 = AsyncMock()
        mock_source2.name = "source2"
        mock_source2.get_stock_info = AsyncMock(
            return_value=StockInfo(
                    code="000001.SZ",
                    name="平安银行",
                    market="SZ",
                    industry="银行",
                    list_date=None,
                )
        )

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source1, mock_source2]

        result = await fetcher.get_stock_info("000001.SZ")

        assert result.code == "000001.SZ"
        mock_source1.get_stock_info.assert_called_once()
        mock_source2.get_stock_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stock_info_all_sources_failed(self, fetcher):
        """测试所有数据源失败"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.make_key = Mock(return_value="test_key")

        mock_source1 = AsyncMock()
        mock_source1.name = "source1"
        mock_source1.get_stock_info = AsyncMock(side_effect=Exception("Failed"))

        mock_source2 = AsyncMock()
        mock_source2.name = "source2"
        mock_source2.get_stock_info = AsyncMock(side_effect=Exception("Failed"))

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source1, mock_source2]

        with pytest.raises(DataSourceError):
            await fetcher.get_stock_info("000001.SZ")


class TestGetDailyQuotes:
    """获取日线行情测试"""

    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()

    @pytest.mark.asyncio
    async def test_get_daily_quotes_from_cache(self, fetcher):
        """测试从缓存获取日线行情"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(
            return_value=[
                {
                    "stock_code": "000001.SZ",
                    "trade_date": "2024-01-01",
                    "open": 10.0,
                    "high": 11.0,
                    "low": 9.0,
                    "close": 10.5,
                    "volume": 1000000,
                    "amount": 10500000.0,
                }
            ]
        )
        mock_cache.make_key = Mock(return_value="test_key")
        fetcher.cache = mock_cache

        result = await fetcher.get_daily_quotes(
            "000001.SZ",
            date(2024, 1, 1),
            date(2024, 1, 31),
        )

        assert len(result) == 1
        assert result[0].stock_code == "000001.SZ"

    @pytest.mark.asyncio
    async def test_get_daily_quotes_from_source(self, fetcher):
        """测试从数据源获取日线行情"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_daily_quotes = AsyncMock(
            return_value=[
                DailyQuote(stock_code="000001.SZ",
                    trade_date="2024-01-01",
                    open=10.0,
                    high=11.0,
                    low=9.0,
                    close=10.5,
                    volume=1000000,
                    amount=10500000.0,
                )
            ]
        )

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]

        with patch(
            "app.data.data_fetcher.DataPreprocessor.clean_daily_quotes"
        ) as mock_clean:
            mock_clean.return_value = [
                DailyQuote(stock_code="000001.SZ",
                    trade_date="2024-01-01",
                    open=10.0,
                    high=11.0,
                    low=9.0,
                    close=10.5,
                    volume=1000000,
                    amount=10500000.0,
                )
            ]

            result = await fetcher.get_daily_quotes(
                "000001.SZ",
                date(2024, 1, 1),
                date(2024, 1, 31),
            )

            assert len(result) == 1
            mock_source.get_daily_quotes.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_daily_quotes_no_cache(self, fetcher):
        """测试不使用缓存"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_daily_quotes = AsyncMock(
            return_value=[
                DailyQuote(stock_code="000001.SZ",
                    trade_date="2024-01-01",
                    open=10.0,
                    high=11.0,
                    low=9.0,
                    close=10.5,
                    volume=1000000,
                    amount=10500000.0,
                )
            ]
        )

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]

        with patch(
            "app.data.data_fetcher.DataPreprocessor.clean_daily_quotes"
        ) as mock_clean:
            mock_clean.return_value = [
                DailyQuote(stock_code="000001.SZ",
                    trade_date="2024-01-01",
                    open=10.0,
                    high=11.0,
                    low=9.0,
                    close=10.5,
                    volume=1000000,
                    amount=10500000.0,
                )
            ]

            _ = await fetcher.get_daily_quotes(
                "000001.SZ",
                date(2024, 1, 1),
                date(2024, 1, 31),
                use_cache=False,
            )

            # 不使用缓存，不应该调用 cache.get
            mock_cache.get.assert_not_called()


class TestGetIntradayQuotes:
    """获取分钟线行情测试"""

    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()

    @pytest.mark.asyncio
    async def test_get_intraday_quotes_from_cache(self, fetcher):
        """测试从缓存获取分钟线行情"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(
            return_value=[
                {
                    "stock_code": "000001.SZ",
                    "time": "09:30:00",
                    "price": 10.0,
                    "volume": 10000,
                }
            ]
        )
        mock_cache.make_key = Mock(return_value="test_key")
        fetcher.cache = mock_cache

        result = await fetcher.get_intraday_quotes("000001.SZ")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_intraday_quotes_from_source(self, fetcher):
        """测试从数据源获取分钟线行情"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_intraday_quotes = AsyncMock(
            return_value=[
                IntradayQuote(
                    code="000001.SZ",
                    time="09:30:00",
                    price=10.0,
                    volume=10000,
                )
            ]
        )

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]

        result = await fetcher.get_intraday_quotes("000001.SZ")

        assert len(result) == 1
        mock_source.get_intraday_quotes.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_intraday_quotes_not_available(self, fetcher):
        """测试分钟线数据不可用"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.make_key = Mock(return_value="test_key")

        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_intraday_quotes = AsyncMock(
            side_effect=Exception("Not available")
        )

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]

        result = await fetcher.get_intraday_quotes("000001.SZ")

        assert result == []


class TestGetFinancialData:
    """获取财务数据测试"""

    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()

    @pytest.mark.asyncio
    async def test_get_financial_data_from_cache(self, fetcher):
        """测试从缓存获取财务数据"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(
            return_value={
                "stock_code": "000001.SZ",
                "report_date": "2024-03-31",
                "revenue": 1000000000.0,
                "net_profit": 100000000.0,
            }
        )
        mock_cache.make_key = Mock(return_value="test_key")
        fetcher.cache = mock_cache

        result = await fetcher.get_financial_data("000001.SZ")

        assert result is not None
        assert result.code == "000001.SZ"

    @pytest.mark.asyncio
    async def test_get_financial_data_from_source(self, fetcher):
        """测试从数据源获取财务数据"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_financial_data = AsyncMock(
            return_value=FinancialData(
                code="000001.SZ",
                report_date="2024-03-31",
                revenue=1000000000.0,
                net_profit=100000000.0,
            )
        )

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]

        result = await fetcher.get_financial_data("000001.SZ")

        assert result is not None
        mock_source.get_financial_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_financial_data_not_found(self, fetcher):
        """测试财务数据不存在"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.make_key = Mock(return_value="test_key")

        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_financial_data = AsyncMock(return_value=None)

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]

        result = await fetcher.get_financial_data("000001.SZ")

        assert result is None


class TestHealthCheck:
    """健康检查测试"""

    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()

    @pytest.mark.asyncio
    async def test_health_check(self, fetcher):
        """测试健康检查"""
        mock_health_checker = AsyncMock()
        mock_health_checker.check_all = AsyncMock(
            return_value={
                "tushare": HealthStatus.HEALTHY,
                "akshare": HealthStatus.HEALTHY,
            }
        )

        fetcher.health_checker = mock_health_checker

        result = await fetcher.health_check()

        assert result["tushare"] == HealthStatus.HEALTHY
        assert result["akshare"] == HealthStatus.HEALTHY


class TestCircuitBreaker:
    """熔断器测试"""

    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()

    @pytest.mark.asyncio
    async def test_get_circuit_breaker_status(self, fetcher):
        """测试获取熔断器状态"""
        mock_registry = Mock()
        mock_registry.get_all_status = Mock(
            return_value={
                "tushare": {"state": "closed", "failure_count": 0},
                "akshare": {"state": "closed", "failure_count": 0},
            }
        )

        fetcher.circuit_registry = mock_registry

        result = await fetcher.get_circuit_breaker_status()

        assert "tushare" in result
        assert "akshare" in result

    @pytest.mark.asyncio
    async def test_reset_circuit_breakers(self, fetcher):
        """测试重置熔断器"""
        mock_registry = Mock()
        mock_registry.reset_all = Mock()

        fetcher.circuit_registry = mock_registry

        await fetcher.reset_circuit_breakers()

        mock_registry.reset_all.assert_called_once()


class TestCacheStats:
    """缓存统计测试"""

    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, fetcher):
        """测试获取缓存统计"""
        mock_cache = AsyncMock()
        mock_cache.get_stats = AsyncMock(
            return_value={
                "local_cache_size": 10,
                "redis_connected": True,
            }
        )

        fetcher.cache = mock_cache

        result = await fetcher.get_cache_stats()

        assert "local_cache_size" in result
        mock_cache.get_stats.assert_called_once()


class TestClose:
    """关闭连接测试"""

    @pytest.mark.asyncio
    async def test_close(self):
        """测试关闭所有连接"""
        fetcher = DataFetcher()

        mock_tushare = AsyncMock()
        mock_tushare.close = AsyncMock()

        mock_cache = AsyncMock()
        mock_cache.close = AsyncMock()

        fetcher.tushare = mock_tushare
        fetcher.cache = mock_cache

        await fetcher.close()

        mock_tushare.close.assert_called_once()
        mock_cache.close.assert_called_once()


# 运行测试
if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=app.data.data_fetcher", "--cov-report=term-missing"]
    )
