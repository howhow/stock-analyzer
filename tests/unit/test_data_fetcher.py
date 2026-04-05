"""数据获取器测试"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.data.data_fetcher import DataFetcher
from app.models.stock import DailyQuote, StockInfo, FinancialData


class TestDataFetcher:
    """数据获取器测试"""

    @pytest.fixture
    def data_fetcher(self):
        """创建数据获取器实例"""
        with patch("app.data.data_fetcher.TushareClient") as mock_tushare, \
             patch("app.data.data_fetcher.AKShareClient") as mock_akshare, \
             patch("app.data.data_fetcher.CacheManager") as mock_cache:
            
            mock_tushare.return_value = AsyncMock()
            mock_akshare.return_value = AsyncMock()
            mock_cache.return_value = MagicMock()
            
            fetcher = DataFetcher()
            return fetcher

    @pytest.mark.asyncio
    async def test_get_stock_info(self, data_fetcher):
        """测试获取股票信息"""
        mock_stock = StockInfo(
            stock_code="000001.SZ",
            name="平安银行",
            industry="金融",
            list_date=date(1991, 4, 3),
        )
        
        data_fetcher.tushare.get_stock_info = AsyncMock(return_value=mock_stock)
        
        result = await data_fetcher.get_stock_info("000001.SZ")
        
        assert result is not None
        assert result.stock_code == "000001.SZ"
        assert result.name == "平安银行"

    @pytest.mark.asyncio
    async def test_get_daily_quotes(self, data_fetcher):
        """测试获取日线数据"""
        mock_quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                close=10.5,
                high=11.0,
                low=9.5,
                volume=1000000,
                amount=10500000,
            )
        ]
        
        data_fetcher.tushare.get_daily_quotes = AsyncMock(return_value=mock_quotes)
        
        result = await data_fetcher.get_daily_quotes(
            "000001.SZ",
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        assert len(result) == 1
        assert result[0].stock_code == "000001.SZ"

    @pytest.mark.asyncio
    async def test_get_financial_data(self, data_fetcher):
        """测试获取财务数据"""
        mock_financial = FinancialData(
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
        
        data_fetcher.tushare.get_financial_data = AsyncMock(return_value=mock_financial)
        
        result = await data_fetcher.get_financial_data("000001.SZ")
        
        assert result is not None
        assert result.stock_code == "000001.SZ"
        assert result.roe == 0.12

    @pytest.mark.asyncio
    async def test_fallback_to_akshare(self, data_fetcher):
        """测试降级到AKShare"""
        mock_quotes = [
            DailyQuote(
                stock_code="000001.SZ",
                trade_date=date(2024, 1, 1),
                open=10.0,
                close=10.5,
                high=11.0,
                low=9.5,
                volume=1000000,
                amount=10500000,
            )
        ]
        
        # Tushare失败
        data_fetcher.tushare.get_daily_quotes = AsyncMock(return_value=[])
        
        # AKShare成功
        data_fetcher.akshare.get_daily_quotes = AsyncMock(return_value=mock_quotes)
        
        result = await data_fetcher.get_daily_quotes(
            "000001.SZ",
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        assert len(result) == 1
        assert result[0].stock_code == "000001.SZ"

    @pytest.mark.asyncio
    async def test_cache_usage(self, data_fetcher):
        """测试缓存使用"""
        mock_stock = StockInfo(
            stock_code="000001.SZ",
            name="平安银行",
            industry="金融",
            list_date=date(1991, 4, 3),
        )
        
        # 设置缓存
        data_fetcher.cache.get = MagicMock(return_value=None)
        data_fetcher.cache.set = MagicMock()
        data_fetcher.tushare.get_stock_info = AsyncMock(return_value=mock_stock)
        
        # 第一次调用
        result1 = await data_fetcher.get_stock_info("000001.SZ")
        
        # 第二次调用（应该从缓存获取）
        data_fetcher.cache.get = MagicMock(return_value=mock_stock)
        result2 = await data_fetcher.get_stock_info("000001.SZ")
        
        assert result1.stock_code == "000001.SZ"
        assert result2.stock_code == "000001.SZ"

    @pytest.mark.asyncio
    async def test_get_trade_calendar(self, data_fetcher):
        """测试获取交易日历"""
        mock_dates = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
        
        data_fetcher.tushare.get_trade_calendar = AsyncMock(return_value=mock_dates)
        
        # 直接测试tushare客户端
        result = await data_fetcher.tushare.get_trade_calendar(2024)
        
        assert len(result) == 3
        assert date(2024, 1, 2) in result

    @pytest.mark.asyncio
    async def test_health_check(self, data_fetcher):
        """测试健康检查"""
        data_fetcher.tushare.health_check = AsyncMock(return_value=True)
        data_fetcher.akshare.health_check = AsyncMock(return_value=True)
        
        # 测试客户端健康检查
        tushare_ok = await data_fetcher.tushare.health_check()
        akshare_ok = await data_fetcher.akshare.health_check()
        
        assert tushare_ok is True
        assert akshare_ok is True
