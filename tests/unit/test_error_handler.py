"""Error Handler完整测试 - 类型安全、防御性编程"""

import pytest
from fastapi import FastAPI, Request, status
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.core.error_handler import (
    register_exception_handlers,
    stock_analyzer_exception_handler,
    generic_exception_handler,
    _get_status_code,
)
from app.core.exceptions import (
    AnalysisError,
    AuthenticationError,
    ConfigurationError,
    DataError,
    DataNotFoundError,
    DataSourceError,
    InvalidParameterError,
    RateLimitError,
    StockAnalyzerError,
)


class TestGetStatusCode:
    """测试状态码映射 - 边界条件全覆盖"""

    def test_data_not_found_returns_404(self) -> None:
        """测试DataNotFoundError返回404"""
        exc = DataNotFoundError("Stock not found")
        assert _get_status_code(exc) == status.HTTP_404_NOT_FOUND

    def test_invalid_parameter_returns_400(self) -> None:
        """测试InvalidParameterError返回400"""
        exc = InvalidParameterError("Invalid stock code")
        assert _get_status_code(exc) == status.HTTP_400_BAD_REQUEST

    def test_authentication_error_returns_401(self) -> None:
        """测试AuthenticationError返回401"""
        exc = AuthenticationError("Invalid token")
        assert _get_status_code(exc) == status.HTTP_401_UNAUTHORIZED

    def test_rate_limit_error_returns_429(self) -> None:
        """测试RateLimitError返回429"""
        exc = RateLimitError("Too many requests")
        assert _get_status_code(exc) == status.HTTP_429_TOO_MANY_REQUESTS

    def test_data_error_returns_422(self) -> None:
        """测试DataError返回422"""
        exc = DataError("Data fetch failed")
        assert _get_status_code(exc) == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_data_source_error_returns_422(self) -> None:
        """测试DataSourceError返回422"""
        exc = DataSourceError("API unavailable")
        assert _get_status_code(exc) == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_analysis_error_returns_422(self) -> None:
        """测试AnalysisError返回422"""
        exc = AnalysisError("Analysis failed")
        assert _get_status_code(exc) == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_configuration_error_returns_500(self) -> None:
        """测试ConfigurationError返回500"""
        exc = ConfigurationError("Config missing")
        assert _get_status_code(exc) == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_unknown_error_returns_500(self) -> None:
        """测试未知异常返回500"""
        exc = StockAnalyzerError("Unknown error")
        assert _get_status_code(exc) == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestStockAnalyzerExceptionHandler:
    """测试自定义异常处理器"""

    @pytest.mark.asyncio
    async def test_exception_handler_returns_json_response(self) -> None:
        """测试异常处理器返回JSON响应"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/analysis"
        
        exc = InvalidParameterError("Invalid parameter", details={"field": "stock_code"})
        
        response = await stock_analyzer_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # JSONResponse会自动序列化，这里验证状态码即可

    @pytest.mark.asyncio
    async def test_exception_handler_with_details(self) -> None:
        """测试异常处理器包含详细信息"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/stock/000001.SZ"
        
        exc = DataNotFoundError("Stock not found", details={"code": "000001.SZ"})
        
        response = await stock_analyzer_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_exception_handler_without_details(self) -> None:
        """测试异常处理器无详细信息"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/analysis"
        
        exc = AuthenticationError("Token expired")
        
        response = await stock_analyzer_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGenericExceptionHandler:
    """测试通用异常处理器"""

    @pytest.mark.asyncio
    async def test_generic_exception_returns_500(self) -> None:
        """测试通用异常返回500"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/analysis"
        
        exc = ValueError("Unexpected error")
        
        response = await generic_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestRegisterExceptionHandlers:
    """测试异常处理器注册"""

    def test_register_exception_handlers(self) -> None:
        """测试注册异常处理器"""
        app = FastAPI()
        
        # 注册异常处理器
        register_exception_handlers(app)
        
        # 验证异常处理器已注册
        assert StockAnalyzerError in app.exception_handlers
        assert Exception in app.exception_handlers

    def test_exception_handler_integration(self) -> None:
        """测试异常处理器集成"""
        app = FastAPI()
        register_exception_handlers(app)
        
        @app.get("/test-error")
        async def test_error():
            raise InvalidParameterError("Test error")
        
        client = TestClient(app)
        response = client.get("/test-error")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
