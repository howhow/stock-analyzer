"""
数据获取协调器最终冲刺测试

目标: 覆盖所有未测试的行，达到 95%
未覆盖行: 90-102, 199, 231-244, 290-302, 323
"""

import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock, patch

from app.data.data_fetcher import DataFetcher
from app.data.base import DataSourceError
from app.models.stock import StockInfo, DailyQuote, IntradayQuote, FinancialData


class TestDataFetcherFinalSprint:
    """数据获取器最终冲刺测试"""
    
    @pytest.mark.asyncio
    async def test_get_stock_info_with_cache_hit(self):
        """测试股票信息缓存命中 - 覆盖行 90-102"""
        fetcher = DataFetcher()
        
        # 模拟缓存命中
        mock_cache_data = {
            "stock_code": "000001.SZ",
            "name": "平安银行",
            "industry": "银行",
            "market_cap": 1000000000.0,
        }
        
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=mock_cache_data)
        mock_cache.make_key = Mock(return_value="test_key")
        
        fetcher.cache = mock_cache
        
        result = await fetcher.get_stock_info("000001.SZ")
        
        assert result.stock_code == "000001.SZ"
    
    @pytest.mark.asyncio
    async def test_get_stock_info_from_source_success(self):
        """测试股票信息从数据源获取成功 - 覆盖行 90-102"""
        fetcher = DataFetcher()
        
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")
        
        # 创建正确的 StockInfo 对象
        stock_info = StockInfo(
            stock_code="000001.SZ",
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
        
        assert result.stock_code == "000001.SZ"
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_daily_quotes_from_source_success(self):
        """测试日线行情从数据源获取成功 - 覆盖行 199"""
        fetcher = DataFetcher()
        
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")
        
        # 创建正确的 DailyQuote 对象
        daily_quote = DailyQuote(
            stock_code="000001.SZ",
            trade_date=date(2024, 1, 1),
            open=10.0,
            high=11.0,
            low=9.0,
            close=10.5,
            volume=1000000,
            amount=10500000.0,
        )
        
        mock_source = AsyncMock()
        mock_source.name = "tushare"
        mock_source.get_daily_quotes = AsyncMock(return_value=[daily_quote])
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        with patch("app.data.data_fetcher.DataPreprocessor.clean_daily_quotes") as mock_clean:
            mock_clean.return_value = [daily_quote]
            
            result = await fetcher.get_daily_quotes(
                "000001.SZ",
                date(2024, 1, 1),
                date(2024, 1, 31),
            )
            
            assert len(result) == 1
            assert result[0].stock_code == "000001.SZ"
    
    @pytest.mark.asyncio
    async def test_get_intraday_quotes_from_source_success(self):
        """测试分钟线行情从数据源获取成功 - 覆盖行 231-244"""
        fetcher = DataFetcher()
        
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")
        
        # 创建正确的 IntradayQuote 对象
        intraday_quote = IntradayQuote(
            stock_code="000001.SZ",
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
        assert result[0].stock_code == "000001.SZ"
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_financial_data_from_source_success(self):
        """测试财务数据从数据源获取成功 - 覆盖行 290-302"""
        fetcher = DataFetcher()
        
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")
        
        # 创建正确的 FinancialData 对象
        financial_data = FinancialData(
            stock_code="000001.SZ",
            report_date=date(2024, 3, 31),
            revenue=1000000000,
            net_profit=100000000,
            total_assets=5000000000,
            total_liabilities=4000000000,
            roe=0.12,
            pe_ratio=10.5,
            pb_ratio=1.2,
            debt_ratio=0.8,
        )
        
        mock_source = AsyncMock()
        mock_source.name = "tushare"
        mock_source.get_financial_data = AsyncMock(return_value=financial_data)
        
        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]
        
        result = await fetcher.get_financial_data("000001.SZ")
        
        assert result is not None
        assert result.stock_code == "000001.SZ"
        mock_cache.set.assert_called_once()


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.data.data_fetcher", "--cov-report=term-missing"])
