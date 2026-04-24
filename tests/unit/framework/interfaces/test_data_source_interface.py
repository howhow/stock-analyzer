"""测试数据源接口协议"""

from datetime import date

import pytest

from framework.models.quote import StandardQuote


class MockDataSource:
    """模拟数据源实现"""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def supported_markets(self) -> list[str]:
        return ["SH", "SZ"]

    async def get_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> list[StandardQuote]:
        return []

    async def get_realtime_quote(self, stock_code: str) -> StandardQuote | None:
        return None

    async def health_check(self) -> bool:
        return True

    async def get_supported_stocks(self, market: str) -> list[str]:
        return []


class TestDataSourceInterface:
    """测试数据源接口"""

    def test_mock_implementation_satisfies_interface(self):
        """验证模拟实现满足接口"""
        mock = MockDataSource()

        # 验证属性
        assert mock.name == "mock"
        assert mock.supported_markets == ["SH", "SZ"]

    @pytest.mark.asyncio
    async def test_get_quotes_returns_list(self):
        """验证 get_quotes 返回列表"""
        mock = MockDataSource()
        quotes = await mock.get_quotes("600519.SH", date(2024, 1, 1), date(2024, 1, 10))
        assert isinstance(quotes, list)

    @pytest.mark.asyncio
    async def test_health_check_returns_bool(self):
        """验证 health_check 返回布尔值"""
        mock = MockDataSource()
        result = await mock.health_check()
        assert isinstance(result, bool)
