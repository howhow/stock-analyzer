"""
AI异常定义

定义AI模块相关的异常类
"""

from app.core.exceptions import StockAnalyzerError


class AIError(StockAnalyzerError):
    """AI相关错误基类"""

    pass


class AIAPIError(AIError):
    """AI API调用错误"""

    pass


class AITimeoutError(AIError):
    """AI超时错误"""

    pass


class AIRateLimitError(AIError):
    """AI限流错误"""

    pass


class AIConfigError(AIError):
    """AI配置错误"""

    pass


class AIModelNotFoundError(AIError):
    """AI模型未找到错误"""

    pass
