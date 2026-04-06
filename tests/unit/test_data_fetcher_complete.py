"""
数据获取协调器完整测试

目标覆盖率: ≥ 95%
当前覆盖率: 71%
"""

import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.data.data_fetcher import DataFetcher
from app.data.base import DataSourceError
from app.models.stock import StockInfo, DailyQuote


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
        mock_cache.get = AsyncMock(return_value={
            "code": "000001.SZ",
            "name": "平安银行",
            "industry": "银行",
            "market_cap": 1000000000.0,
        })
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
        
        mock_tushare = AsyncMock()
        mock_tushare.name = "tushare"
        mock_tushare.get_stock_info = AsyncMock(return_value=StockInfo(
            code="000001.SZ",
            name="平安银行",
            industry="银行",
            market_cap=1000000000.0,
        ))
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_tushare]
        
        result = await fetcher.get_stock_info("000001.SZ")
        
        assert result.code == "000001.SZ"
        mock_tushare.get_stock_info.assert_called_once()
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_stock_info_fallback(self, fetcher):
        """测试数据源降级"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        
        mock_tushare = AsyncMock()
        mock_tushare.name = "tushare"
        mock_tushare.get_stock_info = AsyncMock(side_effect=Exception("Tushare failed"))
        
        mock_akshare = AsyncMock()
        mock_akshare.name = "akshare"
        mock_akshare.get_stock_info = AsyncMock(return_value=StockInfo(
            code="000001.SZ",
            name="平安银行",
            industry="银行",
            market_cap=1000000000.0,
        ))
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_tushare, mock_akshare]
        
        result = await fetcher.get_stock_info("000001.SZ")
        
        assert result.code == "000001.SZ"
        mock_tushare.get_stock_info.assert_called_once()
        mock_akshare.get_stock_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_stock_info_all_sources_failed(self, fetcher):
        """测试所有数据源失败"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        
        mock_tushare = AsyncMock()
        mock_tushare.name = "tushare"
        mock_tushare.get_stock_info = AsyncMock(side_effect=Exception("Failed"))
        
        mock_akshare = AsyncMock()
        mock_akshare.name = "akshare"
        mock_akshare.get_stock_info = AsyncMock(side_effect=Exception("Failed"))
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_tushare, mock_akshare]
        
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
        mock_cache.get = AsyncMock(return_value=[
            {
                "code": "000001.SZ",
                "date": "2024-01-01",
                "open": 10.0,
                "high": 11.0,
                "low": 9.0,
                "close": 10.5,
                "volume": 1000000,
                "amount": 10500000.0,
            }
        ])
        fetcher.cache = mock_cache
        
        result = await fetcher.get_daily_quotes(
            "000001.SZ",
            date(2024, 1, 1),
            date(2024, 1, 31),
        )
        
        assert len(result) == 1
        assert result[0].code == "000001.SZ"
    
    @pytest.mark.asyncio
    async def test_get_daily_quotes_from_source(self, fetcher):
        """测试从数据源获取日线行情"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        
        mock_tushare = AsyncMock()
        mock_tushare.name = "tushare"
        mock_tushare.get_daily_quotes = AsyncMock(return_value=[
            DailyQuote(
                code="000001.SZ",
                date="2024-01-01",
                open=10.0,
                high=11.0,
                low=9.0,
                close=10.5,
                volume=1000000,
                amount=10500000.0,
            )
        ])
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_tushare]
        
        result = await fetcher.get_daily_quotes(
            "000001.SZ",
            date(2024, 1, 1),
            date(2024, 1, 31),
        )
        
        assert len(result) == 1
        mock_tushare.get_daily_quotes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_daily_quotes_no_cache(self, fetcher):
        """测试不使用缓存"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=[{
            "code": "000001.SZ",
            "date": "2024-01-01",
            "open": 10.0,
            "high": 11.0,
            "low": 9.0,
            "close": 10.5,
            "volume": 1000000,
            "amount": 10500000.0,
        }])
        
        mock_tushare = AsyncMock()
        mock_tushare.name = "tushare"
        mock_tushare.get_daily_quotes = AsyncMock(return_value=[])
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_tushare]
        
        result = await fetcher.get_daily_quotes(
            "000001.SZ",
            date(2024, 1, 1),
            date(2024, 1, 31),
            use_cache=False,
        )
        
        # 不使用缓存，应该调用数据源
        mock_tushare.get_daily_quotes.assert_called_once()


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.data.data_fetcher", "--cov-report=term-missing"])
