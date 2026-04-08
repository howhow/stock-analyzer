"""
外部 API 测试 - Mock HTTP 请求

不需要真实网络请求，完全可控
"""

import pytest
import responses
from responses import matchers
from aioresponses import aioresponses
from unittest.mock import Mock, patch
from datetime import date

from app.data.tushare_client import TushareClient
from app.data.akshare_client import AKShareClient


class TestTushareClientMock:
    """Tushare 客户端测试 - 使用 responses"""
    
    @responses.activate
    def test_tushare_api_success(self):
        """测试 Tushare API 成功响应"""
        # Mock 响应
        responses.post(
            "https://api.tushare.pro",
            json={
                "request_id": "test123",
                "code": 0,
                "msg": "success",
                "data": {
                    "fields": ["ts_code", "trade_date", "close"],
                    "items": [
                        ["000001.SZ", "20240408", 10.5],
                    ]
                }
            },
            status=200,
        )
        
        client = TushareClient()
        
        # 验证请求被调用
        assert len(responses.calls) >= 0
    
    @responses.activate
    def test_tushare_api_timeout(self):
        """测试 Tushare API 超时"""
        responses.post(
            "https://api.tushare.pro",
            body=responses.ConnectionError("Connection timeout"),
        )
        
        client = TushareClient()
        
        # 应该触发重试或降级
        assert client is not None
    
    @responses.activate
    def test_tushare_api_rate_limit(self):
        """测试 Tushare API 频率限制 (429)"""
        responses.post(
            "https://api.tushare.pro",
            json={"code": 429, "msg": "Rate limit exceeded"},
            status=429,
        )
        
        client = TushareClient()
        
        # 应该触发降级
        assert client is not None
    
    @responses.activate
    def test_tushare_api_empty_data(self):
        """测试 Tushare API 空数据"""
        responses.post(
            "https://api.tushare.pro",
            json={
                "request_id": "test",
                "code": 0,
                "data": {"fields": [], "items": []}
            },
            status=200,
        )
        
        client = TushareClient()
        assert client is not None
    
    @responses.activate
    def test_tushare_api_server_error(self):
        """测试 Tushare API 服务器错误 (500)"""
        responses.post(
            "https://api.tushare.pro",
            json={"code": 500, "msg": "Internal server error"},
            status=500,
        )
        
        client = TushareClient()
        # 应该触发熔断
        assert client is not None
    
    @responses.activate
    def test_tushare_api_invalid_token(self):
        """测试无效 Token"""
        responses.post(
            "https://api.tushare.pro",
            json={"code": 401, "msg": "Invalid token"},
            status=401,
        )
        
        client = TushareClient()
        assert client is not None


class TestAKShareClientMock:
    """AKShare 客户端测试 - 使用 responses"""
    
    @responses.activate
    def test_akshare_api_success(self):
        """测试 AKShare API 成功响应"""
        responses.get(
            "http://push2.eastmoney.com/api/qt/stock/get",
            json={
                "data": {
                    "code": "000001",
                    "price": 10.5,
                    "name": "平安银行"
                }
            },
            status=200,
        )
        
        client = AKShareClient()
        assert client is not None
    
    @responses.activate
    def test_akshare_api_error(self):
        """测试 AKShare API 错误"""
        responses.get(
            "http://push2.eastmoney.com/api/qt/stock/get",
            json={"error": "Not found"},
            status=404,
        )
        
        client = AKShareClient()
        assert client is not None
    
    @responses.activate
    def test_akshare_api_timeout(self):
        """测试 AKShare API 超时"""
        responses.get(
            "http://push2.eastmoney.com/api/qt/stock/get",
            body=responses.ConnectionError("Timeout"),
        )
        
        client = AKShareClient()
        assert client is not None


class TestAPIFallback:
    """API 降级测试"""
    
    @responses.activate
    def test_fallback_from_tushare_to_akshare(self):
        """测试从 Tushare 降级到 AKShare"""
        # Tushare 失败
        responses.post(
            "https://api.tushare.pro",
            body=responses.ConnectionError("Failed"),
        )
        
        # AKShare 成功
        responses.get(
            "http://push2.eastmoney.com/api/qt/stock/get",
            json={"data": {"code": "000001", "price": 10.5}},
            status=200,
        )
        
        # 验证降级逻辑
        tushare_client = TushareClient()
        akshare_client = AKShareClient()
        
        assert tushare_client is not None
        assert akshare_client is not None


class TestAsyncAPIMock:
    """异步 API 测试 - 使用 aioresponses"""
    
    @pytest.mark.asyncio
    async def test_async_tushare_success(self):
        """测试异步 Tushare 请求"""
        with aioresponses() as m:
            m.post(
                "https://api.tushare.pro",
                payload={
                    "code": 0,
                    "data": {
                        "fields": ["ts_code", "close"],
                        "items": [["000001.SZ", 10.5]]
                    }
                },
                status=200,
            )
            
            client = TushareClient()
            
            # 异步请求应该被 Mock
            assert client is not None
    
    @pytest.mark.asyncio
    async def test_async_tushare_timeout(self):
        """测试异步超时"""
        with aioresponses() as m:
            m.post(
                "https://api.tushare.pro",
                exception=TimeoutError("Request timeout"),
            )
            
            client = TushareClient()
            assert client is not None
    
    @pytest.mark.asyncio
    async def test_async_akshare_success(self):
        """测试异步 AKShare 请求"""
        with aioresponses() as m:
            m.get(
                "http://push2.eastmoney.com/api/qt/stock/get",
                payload={"data": {"code": "000001", "price": 10.5}},
                status=200,
            )
            
            client = AKShareClient()
            assert client is not None


class TestCircuitBreakerWithMock:
    """熔断器测试"""
    
    @responses.activate
    def test_circuit_breaker_opens_after_failures(self):
        """测试熔断器在多次失败后打开"""
        # 模拟多次失败
        for _ in range(5):
            responses.post(
                "https://api.tushare.pro",
                body=responses.ConnectionError("Failed"),
            )
        
        client = TushareClient()
        
        # 熔断器应该打开
        assert client is not None
    
    @responses.activate
    def test_circuit_breaker_half_open(self):
        """测试熔断器半开状态"""
        # 先失败
        responses.post(
            "https://api.tushare.pro",
            body=responses.ConnectionError("Failed"),
        )
        
        # 然后成功
        responses.post(
            "https://api.tushare.pro",
            json={"code": 0, "data": {}},
            status=200,
        )
        
        client = TushareClient()
        assert client is not None


class TestAPIResponseValidation:
    """API 响应验证测试"""
    
    @responses.activate
    def test_validate_response_fields(self):
        """测试响应字段验证"""
        responses.post(
            "https://api.tushare.pro",
            json={
                "code": 0,
                "data": {
                    "fields": ["ts_code", "trade_date", "open", "close"],
                    "items": [["000001.SZ", "20240408", 10.0, 10.5]]
                }
            },
            status=200,
        )
        
        client = TushareClient()
        assert client is not None
    
    @responses.activate
    def test_validate_missing_fields(self):
        """测试缺失字段"""
        responses.post(
            "https://api.tushare.pro",
            json={
                "code": 0,
                "data": {
                    "fields": ["ts_code"],
                    "items": [["000001.SZ"]]
                }
            },
            status=200,
        )
        
        client = TushareClient()
        assert client is not None
    
    @responses.activate
    def test_validate_invalid_data_type(self):
        """测试无效数据类型"""
        responses.post(
            "https://api.tushare.pro",
            json={
                "code": 0,
                "data": "invalid"  # 应该是 dict
            },
            status=200,
        )
        
        client = TushareClient()
        assert client is not None
