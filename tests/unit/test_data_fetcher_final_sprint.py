"""
数据获取协调器最终冲刺测试

目标: 覆盖所有未测试的行，达到 95%
未覆盖行: 90-102, 199, 231-244, 290-302, 323
"""

import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pydantic import ValidationError

from app.data.data_fetcher import DataFetcher
from app.data.base import DataSourceError
from app.models.stock import StockInfo, DailyQuote, IntradayQuote, FinancialData


class TestDataFetcherCacheHit:
    """测试缓存命中场景"""
    
    @pytest.mark.asyncio
    async def test_get_stock_info_cache_hit(self):
        """测试股票信息缓存命中 - 覆盖行 90-102"""
        fetcher = DataFetcher()
        
        # 模拟缓存命中
        mock_cache_data = {
            "code": "000001.SZ",
            "name": "平安银行",
            "industry": "银行",
            "market_cap": 1000000000.0,
        }
        
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=mock_cache_data)
        mock_cache.make_key = Mock(return_value="stock_info:000001.SZ")
        
        fetcher.cache = mock_cache
        
        result = await fetcher.get_stock_info("000001.SZ")
        
        assert result.code == "000001.SZ"
        assert result.name == "平安银行"


class TestDataFetcherSourceSuccess:
    """测试数据源成功场景"""
    
    @pytest.mark.asyncio
    async def test_get_stock_info_source_success(self):
        """测试股票信息从数据源获取成功 - 覆盖行 90-102"""
        fetcher = DataFetcher()
        
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="stock_info:000001.SZ")
        
        # 创建正确的 StockInfo 对象
        stock_info = StockInfo(
            code="000001.SZ",
            name="平安银行",
            industry="银行",
            market_cap=1000000000.0,
        )
        
        mock_source = AsyncMock()
        mock_source.name = "tushare"
        mock_source.get_stock_info = AsyncMock(return_value=stock_info)
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        result = await fetcher.get_stock_info("000001.SZ")
        
        assert result.code == "000001.SZ"
        mock_cache.set.assert_called_once()


class TestDataFetcherIntraday:
    """测试分钟线行情"""
    
    @pytest.mark.asyncio
    async def test_get_intraday_quotes_source_success(self):
        """测试分钟线行情从数据源获取成功 - 覆盖行 231-244"""
        fetcher = DataFetcher()
        
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="intraday_quotes:000001.SZ")
        
        # 创建正确的 IntradayQuote 对象
        intraday_quote = IntradayQuote(
            code="000001.SZ",
            time="09:30:00",
            price=10.0,
            volume=10000,
        )
        
        mock_source = AsyncMock()
        mock_source.name = "tushare"
        mock_source.get_intraday_quotes = AsyncMock(return_value=[intraday_quote])
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        result = await fetcher.get_intraday_quotes("000001.SZ")
        
        assert len(result) == 1
        assert result[0].code == "000001.SZ"
        mock_cache.set.assert_called_once()


class TestDataFetcherFinancial:
    """测试财务数据"""
    
    @pytest.mark.asyncio
    async def test_get_financial_data_source_success(self):
        """测试财务数据从数据源获取成功 - 覆盖行 290-302"""
        fetcher = DataFetcher()
        
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="financial_data:000001.SZ")
        
        # 创建正确的 FinancialData 对象
        financial_data = FinancialData(
            code="000001.SZ",
            report_date="2024-03-31",
            revenue=1000000000.0,
            net_profit=100000000.0,
        )
        
        mock_source = AsyncMock()
        mock_source.name = "tushare"
        mock_source.get_financial_data = AsyncMock(return_value=financial_data)
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        result = await fetcher.get_financial_data("000001.SZ")
        
        assert result is not None
        assert result.code == "000001.SZ"
        mock_cache.set.assert_called_once()


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.data.data_fetcher", "--cov-report=term-missing"])
