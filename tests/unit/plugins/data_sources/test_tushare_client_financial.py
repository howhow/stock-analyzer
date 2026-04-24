"""Test TushareClient financial data methods"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from plugins.data_sources.tushare.client import TushareClient
from plugins.data_sources.tushare.exceptions import TushareNoDataError


def _create_mock_pro(method_name: str, return_value):
    """创建 Mock pro 对象，处理 __name__ 属性"""
    mock_pro = MagicMock()
    mock_method = MagicMock(return_value=return_value)
    mock_method.__name__ = method_name
    setattr(mock_pro, method_name, mock_method)
    return mock_pro


class TestTushareClientFinancial:
    """TushareClient 财务数据方法测试"""

    @pytest.fixture
    def client(self):
        """创建客户端实例（Mock pro api）"""
        with patch.object(TushareClient, "__init__", lambda self, **kwargs: None):
            client = TushareClient()
            client.token = "test_token"
            client.max_retries = 1  # 减少重试次数
            client.timeout = 10
            client._circuit_breaker = MagicMock()
            client._circuit_breaker.can_execute = MagicMock(return_value=True)
            client._circuit_breaker.record_success = MagicMock(return_value=None)
            client._circuit_breaker.record_failure = MagicMock(return_value=None)
            client._circuit_breaker.state = "closed"
            client._last_call_time = 0.0
            client._min_interval = 0.0  # 禁用速率限制
            return client

    @pytest.mark.asyncio
    async def test_get_daily_basic_success(self, client):
        """get_daily_basic: 成功获取每日财务指标"""
        mock_df = pd.DataFrame({
            "ts_code": ["600519.SH"],
            "trade_date": ["20240101"],
            "pe": [30.5],
            "pb": [8.2],
            "turnover_rate": [1.5],
        })

        client._pro = _create_mock_pro("daily_basic", mock_df)

        df = await client.get_daily_basic("600519.SH")

        assert df is not None
        assert len(df) == 1
        assert df["pe"].iloc[0] == 30.5
        assert df["pb"].iloc[0] == 8.2
        client._pro.daily_basic.assert_called_once_with(
            ts_code="600519.SH",
            fields="ts_code,trade_date,pe,pb,turnover_rate",
        )

    @pytest.mark.asyncio
    async def test_get_daily_basic_no_data(self, client):
        """get_daily_basic: 无数据时抛出异常"""
        client._pro = _create_mock_pro("daily_basic", pd.DataFrame())

        with pytest.raises(TushareNoDataError):
            await client.get_daily_basic("600519.SH")

    @pytest.mark.asyncio
    async def test_get_income_success(self, client):
        """get_income: 成功获取利润表数据"""
        mock_df = pd.DataFrame({
            "ts_code": ["600519.SH"],
            "ann_date": ["20240331"],
            "total_revenue": [1500000000.0],
            "n_income": [500000000.0],
        })

        client._pro = _create_mock_pro("income", mock_df)

        df = await client.get_income("600519.SH")

        assert df is not None
        assert len(df) == 1
        assert df["total_revenue"].iloc[0] == 1500000000.0
        client._pro.income.assert_called_once_with(
            ts_code="600519.SH",
            fields="ts_code,ann_date,f_ann_date,end_date,total_revenue,n_income",
        )

    @pytest.mark.asyncio
    async def test_get_income_with_limit(self, client):
        """get_income: 支持 limit 参数"""
        mock_df = pd.DataFrame({
            "ts_code": ["600519.SH"],
            "total_revenue": [1500000000.0],
        })

        client._pro = _create_mock_pro("income", mock_df)

        df = await client.get_income("600519.SH", limit=5)

        assert df is not None
        client._pro.income.assert_called_once_with(
            ts_code="600519.SH",
            fields="ts_code,ann_date,f_ann_date,end_date,total_revenue,n_income",
            limit=5,
        )

    @pytest.mark.asyncio
    async def test_get_income_no_data(self, client):
        """get_income: 无数据时抛出异常"""
        client._pro = _create_mock_pro("income", pd.DataFrame())

        with pytest.raises(TushareNoDataError):
            await client.get_income("600519.SH")

    @pytest.mark.asyncio
    async def test_get_fina_indicator_success(self, client):
        """get_fina_indicator: 成功获取财务指标数据"""
        mock_df = pd.DataFrame({
            "ts_code": ["600519.SH"],
            "ann_date": ["20240331"],
            "roe": [15.5],
            "roe_diluted": [14.8],
        })

        client._pro = _create_mock_pro("fina_indicator", mock_df)

        df = await client.get_fina_indicator("600519.SH")

        assert df is not None
        assert len(df) == 1
        assert df["roe"].iloc[0] == 15.5
        client._pro.fina_indicator.assert_called_once_with(
            ts_code="600519.SH",
            fields="ts_code,ann_date,end_date,roe,roe_diluted",
        )

    @pytest.mark.asyncio
    async def test_get_fina_indicator_no_data(self, client):
        """get_fina_indicator: 无数据时抛出异常"""
        client._pro = _create_mock_pro("fina_indicator", pd.DataFrame())

        with pytest.raises(TushareNoDataError):
            await client.get_fina_indicator("600519.SH")

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_request(self, client):
        """熔断器开启时阻止请求"""
        client._circuit_breaker.can_execute = MagicMock(return_value=False)

        client._pro = _create_mock_pro("daily_basic", pd.DataFrame())

        from plugins.data_sources.tushare.exceptions import TushareCircuitBreakerError

        with pytest.raises(TushareCircuitBreakerError):
            await client.get_daily_basic("600519.SH")
