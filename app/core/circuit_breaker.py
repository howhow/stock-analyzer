"""
熔断器实现

实现熔断器状态机，用于数据源故障降级
"""

import asyncio
import time
from enum import Enum
from typing import Callable, TypeVar

from app.utils.logger import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


class CircuitState(str, Enum):
    """熔断器状态"""

    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreaker:
    """
    熔断器

    状态机：
    CLOSED → OPEN (失败次数达阈值)
    OPEN → HALF_OPEN (超时后试探)
    HALF_OPEN → CLOSED (成功) / OPEN (失败)

    线程安全，支持异步调用
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        timeout_seconds: int = 300,
        success_threshold: int = 1,
    ):
        """
        初始化熔断器

        Args:
            name: 熔断器名称（用于日志）
            failure_threshold: 失败次数阈值，达到后熔断
            timeout_seconds: 熔断超时时间（秒），超时后进入半开状态
            success_threshold: 半开状态下成功次数阈值，达到后恢复
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        return self._state

    @property
    def is_open(self) -> bool:
        """熔断器是否打开（拒绝请求）"""
        return self._state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """熔断器是否关闭（正常状态）"""
        return self._state == CircuitState.CLOSED

    async def can_execute(self) -> bool:
        """
        检查是否可以执行请求

        Returns:
            True: 可以执行
            False: 熔断中，不应执行
        """
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                # 检查是否超时，可以进入半开状态
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                    return True
                return False

            # HALF_OPEN 状态允许试探请求
            return True

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置（进入半开状态）"""
        if self._last_failure_time is None:
            return False
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.timeout_seconds

    def _transition_to_half_open(self) -> None:
        """转换为半开状态"""
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        logger.info(
            "circuit_breaker_half_open",
            name=self.name,
            timeout_seconds=self.timeout_seconds,
        )

    async def record_success(self) -> None:
        """记录成功"""
        async with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._success_count = 0
                    logger.info("circuit_breaker_closed", name=self.name)

    async def record_failure(self) -> None:
        """记录失败"""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # 半开状态下失败，立即熔断
                self._state = CircuitState.OPEN
                logger.warning(
                    "circuit_breaker_reopened",
                    name=self.name,
                    failure_count=self._failure_count,
                )

            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "circuit_breaker_opened",
                    name=self.name,
                    failure_count=self._failure_count,
                    threshold=self.failure_threshold,
                )

    async def call(self, func: Callable[[], T]) -> T:
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数

        Returns:
            函数返回值

        Raises:
            CircuitBreakerOpenError: 熔断器打开
            Exception: 原始异常
        """
        if not await self.can_execute():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")

        try:
            result = await func() if asyncio.iscoroutinefunction(func) else func()
            await self.record_success()
            return result  # type: ignore[no-any-return]
        except Exception:
            await self.record_failure()
            raise


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""

    pass


class CircuitBreakerRegistry:
    """
    熔断器注册表

    管理多个熔断器实例
    """

    _instance: "CircuitBreakerRegistry | None" = None
    _breakers: dict[str, CircuitBreaker]

    def __new__(cls) -> "CircuitBreakerRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._breakers = {}
        return cls._instance

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 3,
        timeout_seconds: int = 300,
    ) -> CircuitBreaker:
        """
        获取或创建熔断器

        Args:
            name: 熔断器名称
            failure_threshold: 失败阈值
            timeout_seconds: 超时时间

        Returns:
            熔断器实例
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                timeout_seconds=timeout_seconds,
            )
        return self._breakers[name]

    def get(self, name: str) -> CircuitBreaker | None:
        """获取熔断器"""
        return self._breakers.get(name)

    def reset_all(self) -> None:
        """重置所有熔断器"""
        for breaker in self._breakers.values():
            breaker._state = CircuitState.CLOSED
            breaker._failure_count = 0
            breaker._success_count = 0
            breaker._last_failure_time = None

    def get_all_status(self) -> dict[str, dict[str, str | int]]:
        """获取所有熔断器状态"""
        return {
            name: {
                "state": breaker.state.value,
                "failure_count": breaker._failure_count,
                "success_count": breaker._success_count,
            }
            for name, breaker in self._breakers.items()
        }
