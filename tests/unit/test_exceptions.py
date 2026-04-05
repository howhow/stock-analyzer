"""Exceptions完整测试 - 类型安全、防御性编程"""

import pytest

from app.core.exceptions import (
    StockAnalyzerError,
    DataError,
    DataNotFoundError,
    DataSourceError,
    InvalidParameterError,
    AuthenticationError,
    RateLimitError,
    AnalysisError,
    ConfigurationError,
)


class TestExceptions:
    """异常测试"""

    def test_stock_analyzer_error(self):
        """测试基础异常"""
        exc = StockAnalyzerError("Test error")
        
        assert exc.message == "Test error"
        # details默认可能是空字典或None
        assert exc.details is None or exc.details == {}

    def test_stock_analyzer_error_with_details(self):
        """测试带详情的异常"""
        exc = StockAnalyzerError("Test error", details={"key": "value"})
        
        assert exc.message == "Test error"
        assert exc.details == {"key": "value"}

    def test_data_error(self):
        """测试数据异常"""
        exc = DataError("Data fetch failed")
        
        assert exc.message == "Data fetch failed"
        assert isinstance(exc, StockAnalyzerError)

    def test_data_not_found_error(self):
        """测试数据未找到异常"""
        exc = DataNotFoundError("Stock not found", details={"code": "000001.SZ"})
        
        assert exc.message == "Stock not found"
        assert exc.details == {"code": "000001.SZ"}

    def test_data_source_error(self):
        """测试数据源异常"""
        exc = DataSourceError("Tushare API unavailable")
        
        assert exc.message == "Tushare API unavailable"

    def test_invalid_parameter_error(self):
        """测试无效参数异常"""
        exc = InvalidParameterError("Invalid stock code", details={"code": "invalid"})
        
        assert exc.message == "Invalid stock code"

    def test_authentication_error(self):
        """测试认证异常"""
        exc = AuthenticationError("Invalid API key")
        
        assert exc.message == "Invalid API key"

    def test_rate_limit_error(self):
        """测试限流异常"""
        exc = RateLimitError("Too many requests", details={"limit": 100})
        
        assert exc.message == "Too many requests"
        assert exc.details == {"limit": 100}

    def test_analysis_error(self):
        """测试分析异常"""
        exc = AnalysisError("Analysis failed")
        
        assert exc.message == "Analysis failed"

    def test_configuration_error(self):
        """测试配置异常"""
        exc = ConfigurationError("Missing configuration")
        
        assert exc.message == "Missing configuration"

    def test_exception_inheritance(self):
        """测试异常继承关系"""
        assert issubclass(DataError, StockAnalyzerError)
        assert issubclass(DataNotFoundError, StockAnalyzerError)
        assert issubclass(DataSourceError, StockAnalyzerError)
        assert issubclass(InvalidParameterError, StockAnalyzerError)
        assert issubclass(AuthenticationError, StockAnalyzerError)
        assert issubclass(RateLimitError, StockAnalyzerError)
        assert issubclass(AnalysisError, StockAnalyzerError)
        assert issubclass(ConfigurationError, StockAnalyzerError)

    def test_exception_str(self):
        """测试异常字符串表示"""
        exc = StockAnalyzerError("Test error")
        
        str_repr = str(exc)
        assert "Test error" in str_repr

    def test_exception_repr(self):
        """测试异常repr表示"""
        exc = StockAnalyzerError("Test error")
        
        repr_str = repr(exc)
        assert isinstance(repr_str, str)
