"""Tushare 数据源异常定义"""


class TushareError(Exception):
    """Tushare 数据源基础异常"""

    def __init__(self, message: str, code: str | None = None):
        """
        初始化异常

        Args:
            message: 错误消息
            code: 错误代码（可选）
        """
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class TushareAuthError(TushareError):
    """认证错误（Token 无效或过期）"""

    def __init__(self, message: str = "Tushare token 无效或已过期"):
        super().__init__(message, code="AUTH_ERROR")


class TushareRateLimitError(TushareError):
    """速率限制错误"""

    def __init__(
        self, message: str = "Tushare API 请求频率超限", retry_after: int | None = None
    ):
        """
        初始化速率限制异常

        Args:
            message: 错误消息
            retry_after: 重试等待时间（秒）
        """
        self.retry_after = retry_after
        super().__init__(message, code="RATE_LIMIT")

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            return f"{base}，请 {self.retry_after} 秒后重试"
        return base


class TushareTimeoutError(TushareError):
    """请求超时错误"""

    def __init__(self, message: str = "Tushare API 请求超时"):
        super().__init__(message, code="TIMEOUT")


class TushareNoDataError(TushareError):
    """无数据错误"""

    def __init__(self, message: str = "未找到数据"):
        super().__init__(message, code="NO_DATA")


class TushareCircuitBreakerError(TushareError):
    """熔断器开启错误"""

    def __init__(self, message: str = "Tushare 服务熔断中"):
        super().__init__(message, code="CIRCUIT_BREAKER")
