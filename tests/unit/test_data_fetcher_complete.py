"""
DataFetcher 完整测试
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.data.data_fetcher import DataFetcher
from app.data.base import DataSourceError
from app.models.stock import StockInfo, DailyQuote, FinancialData
from app.core.cache import CacheManager


class TestDataFetcherComplete:
    """DataFetcher完整测试"""

    @pytest.fixture
    def mock_tushare(self):
        """Mock Tushare客户端"""
        client = MagicMock()
        client.name = "tushare"
        client.get_stock_info = AsyncMock(
            return_value=StockInfo(
                code="600519.SH",
                name="贵州茅台",
                market="SH",
                industry="白酒",
            )
        )
        client.get_daily_quotes = AsyncMock(
            return_value=[
                DailyQuote(
                    stock_code="600519.SH",
                    trade_date=date(2024, 1, 1),
                    open=100.0,
                    close=101.0,
                    high=102.0,
                    low=99.0,
                    volume=100000,
                    amount=10000000,
                )
            ]
        )
        client.get_financial_data = AsyncMock(
            return_value=FinancialData(
                stock_code="600519.SH",
                report_date=date(2024, 1, 1),
                revenue=1000000000,
                net_profit=100000000,
            )
        )
        client.health_check = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    def mock_akshare(self):
        """Mock AKShare客户端"""
        client = MagicMock()
        client.name = "akshare"
        client.get_stock_info = AsyncMock(side_effect=DataSourceError("Not available"))
        client.get_daily_quotes = AsyncMock(return_value=[])
        client.get_financial_data = AsyncMock(return_value=None)
        client.health_check = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    def mock_cache(self):
        """Mock缓存"""
        cache = MagicMock(spec=CacheManager)
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        cache.make_key = MagicMock(return_value="test_key")
        cache.get_stats = AsyncMock(return_value={"local_cache_size": 0})
        cache.close = AsyncMock()
        return cache

    @pytest.mark.asyncio
    async def test_get_stock_info_from_tushare(
        self, mock_tushare, mock_akshare, mock_cache
    ):
        """测试从Tushare获取股票信息"""
        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        result = await fetcher.get_stock_info("600519.SH")

        assert result.code == "600519.SH"
        assert result.name == "贵州茅台"
        mock_tushare.get_stock_info.assert_called_once_with("600519.SH")
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stock_info_fallback_to_akshare(self, mock_tushare, mock_cache):
        """测试Tushare失败后降级到AKShare"""
        mock_tushare.get_stock_info = AsyncMock(side_effect=DataSourceError("Failed"))
        mock_akshare = MagicMock()
        mock_akshare.name = "akshare"
        mock_akshare.get_stock_info = AsyncMock(
            return_value=StockInfo(
                code="600519.SH",
                name="茅台",
                market="SH",
            )
        )

        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        result = await fetcher.get_stock_info("600519.SH")

        assert result.name == "茅台"
        mock_tushare.get_stock_info.assert_called_once()
        mock_akshare.get_stock_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stock_info_from_cache(self, mock_tushare, mock_akshare):
        """测试从缓存获取股票信息"""
        mock_cache = MagicMock(spec=CacheManager)
        cached_data = {
            "code": "600519.SH",
            "name": "贵州茅台",
            "market": "SH",
            "industry": "白酒",
        }
        mock_cache.get = AsyncMock(return_value=cached_data)
        mock_cache.make_key = MagicMock(return_value="cache_key")

        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        result = await fetcher.get_stock_info("600519.SH")

        assert result.code == "600519.SH"
        mock_cache.get.assert_called_once()
        # 不应该调用数据源
        mock_tushare.get_stock_info.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_stock_info_all_sources_failed(self, mock_cache):
        """测试所有数据源都失败"""
        mock_tushare = MagicMock()
        mock_tushare.name = "tushare"
        mock_tushare.get_stock_info = AsyncMock(side_effect=DataSourceError("Failed"))

        mock_akshare = MagicMock()
        mock_akshare.name = "akshare"
        mock_akshare.get_stock_info = AsyncMock(side_effect=DataSourceError("Failed"))

        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        with pytest.raises(DataSourceError) as exc:
            await fetcher.get_stock_info("600519.SH")

        assert "All data sources failed" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_daily_quotes_success(
        self, mock_tushare, mock_akshare, mock_cache
    ):
        """测试获取日线数据"""
        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        result = await fetcher.get_daily_quotes(
            "600519.SH",
            date(2024, 1, 1),
            date(2024, 1, 31),
        )

        assert len(result) == 1
        assert result[0].stock_code == "600519.SH"

    @pytest.mark.asyncio
    async def test_get_daily_quotes_no_cache(
        self, mock_tushare, mock_akshare, mock_cache
    ):
        """测试不使用缓存获取日线数据"""
        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        result = await fetcher.get_daily_quotes(
            "600519.SH",
            date(2024, 1, 1),
            date(2024, 1, 31),
            use_cache=False,
        )

        assert len(result) == 1
        mock_cache.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_financial_data_success(
        self, mock_tushare, mock_akshare, mock_cache
    ):
        """测试获取财务数据"""
        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        result = await fetcher.get_financial_data("600519.SH")

        assert result is not None
        assert result.stock_code == "600519.SH"
        assert result.revenue == 1000000000

    @pytest.mark.asyncio
    async def test_get_financial_data_not_found(self, mock_tushare, mock_cache):
        """测试财务数据不存在"""
        mock_tushare.get_financial_data = AsyncMock(return_value=None)
        mock_akshare = MagicMock()
        mock_akshare.name = "akshare"
        mock_akshare.get_financial_data = AsyncMock(return_value=None)

        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        result = await fetcher.get_financial_data("999999.SH")

        assert result is None

    @pytest.mark.asyncio
    async def test_health_check(self, mock_tushare, mock_akshare, mock_cache):
        """测试健康检查"""
        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        result = await fetcher.health_check()

        assert "tushare" in result
        assert "akshare" in result

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, mock_tushare, mock_akshare, mock_cache):
        """测试获取缓存统计"""
        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        result = await fetcher.get_cache_stats()

        assert "local_cache_size" in result

    @pytest.mark.asyncio
    async def test_close(self, mock_tushare, mock_akshare, mock_cache):
        """测试关闭连接"""
        mock_tushare.close = AsyncMock()

        fetcher = DataFetcher(
            tushare_client=mock_tushare,
            akshare_client=mock_akshare,
            cache=mock_cache,
        )

        await fetcher.close()

        mock_tushare.close.assert_called_once()
        mock_cache.close.assert_called_once()
