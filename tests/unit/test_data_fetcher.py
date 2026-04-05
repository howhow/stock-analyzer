"""数据获取器测试 - 简化版"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.stock import DailyQuote, StockInfo, FinancialData


class TestStockModels:
    """股票模型测试"""

    def test_stock_info(self):
        """测试股票信息模型"""
        stock = StockInfo(
            code="000001.SZ",
            name="平安银行",
            market="SZ",
            industry="金融",
            list_date=date(1991, 4, 3),
        )
        assert stock.code == "000001.SZ"
        assert stock.name == "平安银行"
        assert stock.market == "SZ"

    def test_daily_quote(self):
        """测试日线数据模型"""
        quote = DailyQuote(
            stock_code="000001.SZ",
            trade_date=date(2024, 1, 1),
            open=10.0,
            close=10.5,
            high=11.0,
            low=9.5,
            volume=1000000,
            amount=10500000,
        )
        assert quote.stock_code == "000001.SZ"
        assert quote.close == 10.5

    def test_financial_data(self):
        """测试财务数据模型"""
        financial = FinancialData(
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
        assert financial.stock_code == "000001.SZ"
        assert financial.roe == 0.12
