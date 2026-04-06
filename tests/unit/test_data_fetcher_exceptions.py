"""
数据获取协调器异常路径测试

目标: 覆盖未测试的异常路径
"""

import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock, patch

from app.data.data_fetcher import DataFetcher
from app.data.base import DataSourceError
from app.models.stock import StockInfo, DailyQuote


class TestDataFetcherExceptionPaths:
    """数据获取器异常路径测试"""
    
    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()
    
    @pytest.mark.asyncio
    async def test_get_stock_info_cache_set_exception(self, fetcher):
        """测试缓存设置异常"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(side_effect=Exception("Cache set failed"))
        mock_cache.make_key = Mock(return_value="test_key")
        
        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_stock_info = AsyncMock(return_value=StockInfo(
            code="000001.SZ",
            name="平安银行",
            industry="银行",
            market_cap=1000000000.0,
        ))
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        # 应该不抛出异常，返回数据
        result = await fetcher.get_stock_info("000001.SZ")
        assert result.code == "000001.SZ"
    
    @pytest.mark.asyncio
    async def test_get_daily_quotes_empty_result(self, fetcher):
        """测试日线行情空结果"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.make_key = Mock(return_value="test_key")
        
        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_daily_quotes = AsyncMock(return_value=[])
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        with pytest.raises(DataSourceError):
            await fetcher.get_daily_quotes(
                "000001.SZ",
                date(2024, 1, 1),
                date(2024, 1, 31),
            )
    
    @pytest.mark.asyncio
    async def test_get_daily_quotes_source_exception(self, fetcher):
        """测试日线行情数据源异常"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.make_key = Mock(return_value="test_key")
        
        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_daily_quotes = AsyncMock(side_effect=Exception("Source failed"))
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        with pytest.raises(DataSourceError):
            await fetcher.get_daily_quotes(
                "000001.SZ",
                date(2024, 1, 1),
                date(2024, 1, 31),
            )
    
    @pytest.mark.asyncio
    async def test_get_intraday_quotes_source_exception(self, fetcher):
        """测试分钟线行情数据源异常"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.make_key = Mock(return_value="test_key")
        
        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_intraday_quotes = AsyncMock(side_effect=Exception("Source failed"))
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        # 分钟线数据失败应该返回空列表
        result = await fetcher.get_intraday_quotes("000001.SZ")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_financial_data_source_exception(self, fetcher):
        """测试财务数据数据源异常"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.make_key = Mock(return_value="test_key")
        
        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_financial_data = AsyncMock(side_effect=Exception("Source failed"))
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        # 财务数据失败应该返回 None
        result = await fetcher.get_financial_data("000001.SZ")
        assert result is None


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.data.data_fetcher", "--cov-report=term-missing"])
