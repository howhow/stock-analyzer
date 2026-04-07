"""
数据获取协调器成功路径测试

目标: 覆盖所有成功路径的代码行，达到 95%
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


class TestDataFetcherSuccessPaths:
    """数据获取器成功路径测试"""

    @pytest.fixture
    def fetcher(self):
        """创建数据获取器"""
        return DataFetcher()

    @pytest.mark.asyncio
    async def test_get_stock_info_success_path(self, fetcher):
        """测试股票信息成功路径 - 覆盖行 90-102"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

        stock_info = StockInfo(
            code="000001.SZ", name="平安银行", market="SZ", industry="银行"
        )

        mock_source = AsyncMock()
        mock_source.name = "tushare"
        mock_source.get_stock_info = AsyncMock(return_value=stock_info)

        fetcher.cache = mock_cache
        fetcher.sources = [mock_source]

        result = await fetcher.get_stock_info("000001.SZ")

        # 验证返回结果
        assert result.code == "000001.SZ"
        assert result.name == "平安银行"

        # 验证缓存写入被调用
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_daily_quotes_success_path(self, fetcher):
        """测试日线行情成功路径 - 覆盖行 199"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

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

        with patch(
            "app.data.data_fetcher.DataPreprocessor.clean_daily_quotes"
        ) as mock_clean:
            mock_clean.return_value = [daily_quote]

            result = await fetcher.get_daily_quotes(
                "000001.SZ",
                date(2024, 1, 1),
                date(2024, 1, 31),
            )

            # 验证返回结果
            assert len(result) == 1
            assert result[0].stock_code == "000001.SZ"

            # 验证缓存写入被调用
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_intraday_quotes_success_path(self, fetcher):
        """测试分钟线行情成功路径 - 覆盖行 231-244"""
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

        # 验证返回结果
        assert len(result) == 1
        assert result[0].stock_code == "000001.SZ"

        # 验证缓存写入被调用
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_financial_data_success_path(self, fetcher):
        """测试财务数据成功路径 - 覆盖行 290-302"""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.make_key = Mock(return_value="test_key")

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

        # 验证返回结果
        assert result is not None
        assert result.stock_code == "000001.SZ"

        # 验证缓存写入被调用
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self, fetcher):
        """测试健康检查成功 - 覆盖行 323"""
        mock_health_checker = AsyncMock()
        mock_health_checker.check_all = AsyncMock(
            return_value={
                "tushare": HealthStatus.HEALTHY,
                "akshare": HealthStatus.HEALTHY,
            }
        )

        fetcher.health_checker = mock_health_checker

        result = await fetcher.health_check()

        # 验证返回结果
        assert result["tushare"] == HealthStatus.HEALTHY
        assert result["akshare"] == HealthStatus.HEALTHY

        # 验证健康检查被调用
        mock_health_checker.check_all.assert_called_once()


# 运行测试
if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=app.data.data_fetcher", "--cov-report=term-missing"]
    )
