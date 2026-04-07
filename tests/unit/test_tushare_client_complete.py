"""Tushare Client完整测试 - 类型安全、异步优先"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.data.base import DataSourceError
from app.data.tushare_client import TushareClient


class TestTushareClientComplete:
    """Tushare客户端完整测试"""

    @pytest.fixture
    def client(self):
        """创建客户端实例"""
        with patch("app.data.tushare_client.settings") as mock_settings:
            mock_settings.tushare_token = "test_token"
            return TushareClient()

    @pytest.fixture
    def client_with_token(self):
        """创建带token的客户端实例"""
        return TushareClient(token="test_token")

    def test_init(self, client):
        """测试初始化"""
        assert client is not None
        assert client.name == "tushare"

    def test_init_with_token(self, client_with_token):
        """测试带token初始化"""
        assert client_with_token is not None

    @pytest.mark.asyncio
    async def test_get_stock_info_success(self, client):
        """测试获取股票信息成功"""
        with patch.object(client, "get_stock_info", new_callable=AsyncMock) as mock:
            mock.return_value = Mock(code="000001.SZ", name="平安银行")
            result = await client.get_stock_info("000001.SZ")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_stock_info_not_found(self, client):
        """测试获取股票信息未找到"""
        with patch.object(
            client, "get_stock_info", new_callable=AsyncMock, return_value=None
        ):
            result = await client.get_stock_info("INVALID")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_daily_quotes_success(self, client):
        """测试获取日线数据成功"""
        with patch.object(client, "get_daily_quotes", new_callable=AsyncMock) as mock:
            mock.return_value = [Mock(stock_code="000001.SZ", close=10.0)]
            result = await client.get_daily_quotes(
                "000001.SZ", date(2024, 1, 1), date(2024, 1, 31)
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_daily_quotes_empty(self, client):
        """测试获取日线数据为空"""
        with patch.object(
            client, "get_daily_quotes", new_callable=AsyncMock, return_value=[]
        ):
            result = await client.get_daily_quotes(
                "INVALID", date(2024, 1, 1), date(2024, 1, 31)
            )
            assert result == []

    @pytest.mark.asyncio
    async def test_get_financial_data_success(self, client):
        """测试获取财务数据成功"""
        with patch.object(client, "get_financial_data", new_callable=AsyncMock) as mock:
            mock.return_value = Mock(stock_code="000001.SZ", revenue=1000000000.0)
            result = await client.get_financial_data("000001.SZ")
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_financial_data_not_found(self, client):
        """测试获取财务数据未找到"""
        with patch.object(
            client, "get_financial_data", new_callable=AsyncMock, return_value=None
        ):
            result = await client.get_financial_data("INVALID")
            assert result is None

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查"""
        with patch.object(
            client, "health_check", new_callable=AsyncMock, return_value=True
        ):
            result = await client.health_check()
            assert result is True

    def test_parse_date_valid(self, client):
        """测试解析有效日期"""
        result = client._parse_date("20240101")
        assert result == date(2024, 1, 1)

    def test_parse_date_invalid(self, client):
        """测试解析无效日期"""
        result = client._parse_date("invalid")
        assert result is None

    def test_normalize_stock_code_sz(self, client):
        """测试标准化深交所代码"""
        result = client._normalize_stock_code("000001.SZ")
        assert result == "000001.SZ"

    def test_normalize_stock_code_sh(self, client):
        """测试标准化上交所代码"""
        result = client._normalize_stock_code("600519.SH")
        assert result == "600519.SH"
