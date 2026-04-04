"""
统一错误处理
"""

# mypy: disable-error-code="arg-type"

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

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
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def stock_analyzer_exception_handler(
    request: Request, exc: StockAnalyzerError
) -> JSONResponse:
    """
    处理所有自定义异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON 响应
    """
    logger.error(
        "exception_occurred",
        exception_type=type(exc).__name__,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
    )

    # 根据异常类型确定状态码
    status_code = _get_status_code(exc)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "details": exc.details if exc.details else None,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON 响应
    """
    logger.exception(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": None,
        },
    )


def _get_status_code(exc: StockAnalyzerError) -> int:
    """根据异常类型获取 HTTP 状态码"""
    if isinstance(exc, DataNotFoundError):
        return status.HTTP_404_NOT_FOUND
    elif isinstance(exc, InvalidParameterError):
        return status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, AuthenticationError):
        return status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, RateLimitError):
        return status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exc, (DataError, DataSourceError, AnalysisError)):
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, ConfigurationError):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        return status.HTTP_500_INTERNAL_SERVER_ERROR


def register_exception_handlers(app: "FastAPI") -> None:
    """
    注册异常处理器

    Args:
        app: FastAPI 应用实例
    """
    app.add_exception_handler(
        StockAnalyzerError, stock_analyzer_exception_handler
    )
    app.add_exception_handler(Exception, generic_exception_handler)
