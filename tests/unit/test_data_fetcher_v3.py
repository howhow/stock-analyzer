"""
数据获取协调器最终测试

目标: 覆盖所有未测试的行，达到 95%
"""

import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock, patch

from app.data.data_fetcher import DataFetcher
from app.models.stock import StockInfo, DailyQuote, IntradayQuote, FinancialData


class TestDataFetcherFinal:
    """数据获取器最终测试"""
    
    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()
    
    @pytest.mark.asyncio
    async def test_get_stock_info_with_cache_hit(self, fetcher):
        """测试股票信息缓存命中"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value={
            "code": "000001.SZ",
            "name": "平安银行",
            "industry": "银行",
            "market_cap": 1000000000.0,
        })
        mock_cache.make_key = Mock(return_value="test_key")
        
        fetcher.cache = mock_cache
        
        result = await fetcher.get_stock_info("000001.SZ")
        
        assert result.code == "000001.SZ"
        mock_cache.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_stock_info_source_success(self, fetcher):
        """测试股票信息从数据源获取成功"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
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
        
        result = await fetcher.get_stock_info("000001.SZ")
        
        assert result.code == "000001.SZ"
        mock_source.get_stock_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_intraday_quotes_with_data(self, fetcher):
        """测试分钟线行情有数据"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")
        
        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_intraday_quotes = AsyncMock(return_value=[
            IntradayQuote(
                code="000001.SZ",
                time="09:30:00",
                price=10.0,
                volume=10000,
            )
        ])
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        result = await fetcher.get_intraday_quotes("000001.SZ")
        
        assert len(result) == 1
        mock_source.get_intraday_quotes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_intraday_quotes_empty_result(self, fetcher):
        """测试分钟线行情无数据"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.make_key = Mock(return_value="test_key")
        
        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_intraday_quotes = AsyncMock(return_value=[])
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        result = await fetcher.get_intraday_quotes("000001.SZ")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_financial_data_with_data(self, fetcher):
        """测试财务数据有数据"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")
        
        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_financial_data = AsyncMock(return_value=FinancialData(
            code="000001.SZ",
            report_date="2024-03-31",
            revenue=1000000000.0,
            net_profit=100000000.0,
        ))
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        result = await fetcher.get_financial_data("000001.SZ")
        
        assert result is not None
        mock_source.get_financial_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_financial_data_source_exception(self, fetcher):
        """测试财务数据源异常"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.make_key = Mock(return_value="test_key")
        
        mock_source = AsyncMock()
        mock_source.name = "test_source"
        mock_source.get_financial_data = AsyncMock(side_effect=Exception("Failed"))
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        result = await fetcher.get_financial_data("000001.SZ")
        
        assert result is None


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.data.data_fetcher", "--cov-report=term-missing"])
