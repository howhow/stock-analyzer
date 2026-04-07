"""
数据获取协调器最后的冲刺测试 - 修正版

目标: 覆盖所有未覆盖的行，达到 95%
未覆盖行: 90-102, 199, 231-244, 323
"""

from datetime import date
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.data.data_fetcher import DataFetcher
from app.data.health_check import HealthStatus
from app.models.stock import DailyQuote, FinancialData, IntradayQuote, StockInfo
from tests.fixtures.mock_data import (
    MOCK_DAILY_QUOTES_DICT,
    MOCK_STOCK_INFO_DICT,
    create_daily_quote_dict,
    create_stock_info_dict,
)


class TestFinalPush:
    """最后的冲刺测试"""

    @pytest.mark.asyncio
    async def test_stock_info_success_with_cache_set(self):
        """测试股票信息成功并设置缓存 - 覆盖行 90-102"""
        fetcher = DataFetcher()

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

        # 使用正确的字段名: code, name, market
        stock_info = StockInfo(
            code="000001.SZ",
            name="平安银行",
            market="SZ",
            industry="银行",
            list_date=None,
        )

        mock_source = AsyncMock()
        mock_source.name = "tushare"
        mock_source.get_stock_info = AsyncMock(return_value=stock_info)

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]

        result = await fetcher.get_stock_info("000001.SZ")

        # 验证结果
        assert result.code == "000001.SZ"
        # 验证缓存设置被调用 - 覆盖行 90-94
        assert mock_cache.set.called

    @pytest.mark.asyncio
    async def test_daily_quotes_success_return(self):
        """测试日线行情成功返回 - 覆盖行 199"""
        fetcher = DataFetcher()

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

        daily_quote = DailyQuote(
            stock_code="000001.SZ",
            trade_trade_date=date(2024, 1, 1),
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

        with patch(
            "app.data.data_fetcher.DataPreprocessor.clean_daily_quotes"
        ) as mock_clean:
            mock_clean.return_value = [daily_quote]

            result = await fetcher.get_daily_quotes(
                "000001.SZ",
                date(2024, 1, 1),
                date(2024, 1, 31),
            )

            # 验证返回 - 覆盖行 199
            assert len(result) == 1
            assert result[0].stock_code == "000001.SZ"

    @pytest.mark.asyncio
    async def test_intraday_quotes_success_with_cache_set(self):
        """测试分钟线行情成功并设置缓存 - 覆盖行 231-244"""
        fetcher = DataFetcher()

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

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

        # 验证结果
        assert len(result) == 1
        # 验证缓存设置被调用 - 覆盖行 231-235
        assert mock_cache.set.called

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """测试健康检查成功 - 覆盖行 323"""
        fetcher = DataFetcher()

        mock_health_checker = AsyncMock()
        mock_health_checker.check_all = AsyncMock(
            return_value={
                "tushare": HealthStatus.HEALTHY,
                "akshare": HealthStatus.HEALTHY,
            }
        )

        fetcher.health_checker = mock_health_checker

        result = await fetcher.health_check()

        # 验证结果 - 覆盖行 323
        assert "tushare" in result
        assert "akshare" in result
        mock_health_checker.check_all.assert_called_once()


# 运行测试
if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=app.data.data_fetcher", "--cov-report=term-missing"]
    )
