"""
AI协议适配器基类

定义所有AI协议适配器必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from pydantic import BaseModel


class AIAnalysisRequest(BaseModel):
    """AI分析请求"""

    prompt: str
    """分析提示词"""

    model: str | None = None
    """模型名称（可选，使用默认模型）"""

    temperature: float = 0.7
    """温度参数（0-1）"""

    max_tokens: int = 2000
    """最大token数"""

    config: dict[str, Any] | None = None
    """额外配置参数"""


class AIAnalysisResponse(BaseModel):
    """AI分析响应"""

    content: str
    """AI返回的内容"""

    model: str
    """使用的模型"""

    usage: dict[str, int] | None = None
    """Token使用情况"""

    latency_ms: float | None = None
    """响应延迟（毫秒）"""


class AIProviderProtocol(Protocol):
    """
    AI协议适配器基类

    所有AI协议适配器必须实现此接口
    """

    async def analyze(
        self,
        request: AIAnalysisRequest,
    ) -> AIAnalysisResponse:
        """
        执行AI分析

        Args:
            request: 分析请求

        Returns:
            分析响应

        Raises:
            AIAPIError: API调用失败
            AITimeoutError: 超时
            AIRateLimitError: 限流
        """
        ...

    async def test_connection(self) -> dict[str, Any]:
        """
        测试连接

        Returns:
            连接状态信息

        Raises:
            AIAPIError: 连接失败
        """
        ...


class BaseAIProvider(ABC):
    """
    AI协议适配器基类（抽象类）

    提供通用功能：
    - 重试机制
    - 超时控制
    - 错误处理
    - 日志记录
    """

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        default_model: str | None = None,
        timeout: float = 20.0,
        max_retries: int = 3,
    ):
        """
        初始化

        Args:
            api_key: API密钥
            base_url: API基础URL（可选）
            default_model: 默认模型
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def analyze(
        self,
        request: AIAnalysisRequest,
    ) -> AIAnalysisResponse:
        """执行AI分析"""
        pass

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """测试连接"""
        pass
