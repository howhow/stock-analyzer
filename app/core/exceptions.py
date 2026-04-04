"""
异常定义模块

所有自定义异常的基类和具体异常类型
"""

from typing import Any


class StockAnalyzerError(Exception):
    """
    基础异常类

    所有系统异常的基类
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# ============ 数据相关异常 ============


class DataError(StockAnalyzerError):
    """数据错误基类"""

    pass


class DataNotFoundError(DataError):
    """数据不存在"""

    pass


class DataValidationError(DataError):
    """数据验证失败"""

    pass


class DataSourceError(DataError):
    """数据源错误"""

    pass


class DataSourceTimeoutError(DataSourceError):
    """数据源超时"""

    pass


class DataSourceRateLimitError(DataSourceError):
    """数据源限流"""

    pass


class DataSourceUnavailableError(DataSourceError):
    """数据源不可用"""

    pass


# ============ 分析相关异常 ============


class AnalysisError(StockAnalyzerError):
    """分析错误基类"""

    pass


class InvalidParameterError(AnalysisError):
    """无效参数"""

    pass


class AnalysisTimeoutError(AnalysisError):
    """分析超时"""

    pass


class AnalysisNotSupportedError(AnalysisError):
    """不支持的分析类型"""

    pass


# ============ 缓存相关异常 ============


class CacheError(StockAnalyzerError):
    """缓存错误基类"""

    pass


class CacheConnectionError(CacheError):
    """缓存连接错误"""

    pass


class CacheKeyError(CacheError):
    """缓存键错误"""

    pass


# ============ 配置相关异常 ============


class ConfigurationError(StockAnalyzerError):
    """配置错误"""

    pass


# ============ 认证相关异常 ============


class AuthenticationError(StockAnalyzerError):
    """认证错误基类"""

    pass


class InvalidTokenError(AuthenticationError):
    """无效Token"""

    pass


class TokenExpiredError(AuthenticationError):
    """Token过期"""

    pass


class PermissionDeniedError(AuthenticationError):
    """权限不足"""

    pass


# ============ 限流相关异常 ============


class RateLimitError(StockAnalyzerError):
    """限流错误"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, details)


# ============ AI 相关异常 ============


class AIError(StockAnalyzerError):
    """AI 错误基类"""

    pass


class AIQuotaExceededError(AIError):
    """AI 配额超限"""

    pass


class AIProviderError(AIError):
    """AI 提供商错误"""

    pass
