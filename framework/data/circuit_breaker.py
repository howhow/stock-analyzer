"""熔断器 — 保护数据源，失败 N 次后熔断，超时后半开恢复

状态机:
- Closed: 正常状态，允许所有请求
- Open: 熔断状态，拒绝所有请求
- Half-Open: 半开状态，允许有限试探请求

状态转换:
- Closed → Open: 连续失败次数达到阈值
- Open → Half-Open: 超过恢复超时时间
- Half-Open → Closed: 试探请求成功
- Half-Open → Open: 试探请求失败

设计原则:
- 线程安全（使用 threading.Lock）
- Half-Open 试探：允许 1 次试探请求
- 与 EventBus 集成，发送熔断事件
"""

import time
import threading
from typing import Dict, Literal
from enum import Enum

from framework.events import Events


class CircuitState(str, Enum):
    """熔断器状态"""

    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态（试探）


class CircuitBreaker:
    """熔断器 — 保护数据源，失败 N 次后熔断，超时后半开恢复

    使用方式:
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

        # 检查是否应该重试
        if breaker.should_retry("tushare"):
            try:
                data = await fetch_data()
                breaker.record_success("tushare")
            except Exception as e:
                breaker.record_failure("tushare")
                raise

    Args:
        failure_threshold: 连续失败次数阈值，达到后熔断（默认 3）
        recovery_timeout: 恢复超时时间（秒），超时后进入 Half-Open（默认 60）
        half_open_max_calls: Half-Open 状态下最大试探次数（默认 1）
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max_calls = half_open_max_calls

        # 每个数据源的独立状态
        self._failure_counts: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}
        self._states: Dict[str, CircuitState] = {}
        self._half_open_calls: Dict[str, int] = {}

        # 线程锁
        self._lock = threading.Lock()

    def should_retry(self, source_name: str) -> bool:
        """是否应该重试

        状态判断逻辑:
        - Closed: 允许请求
        - Open: 检查是否超时，超时则转 Half-Open 并允许试探
        - Half-Open: 检查试探次数，未达上限则允许

        Args:
            source_name: 数据源名称

        Returns:
            True: 允许请求
            False: 拒绝请求（已熔断）
        """
        with self._lock:
            state = self._get_state(source_name)

            if state == CircuitState.CLOSED:
                return True

            elif state == CircuitState.OPEN:
                # 检查是否超时
                last_failure = self._last_failure_time.get(source_name, 0)
                elapsed = time.time() - last_failure

                if elapsed >= self._recovery_timeout:
                    # 超时，转 Half-Open
                    self._states[source_name] = CircuitState.HALF_OPEN
                    # 设置试探次数为 1（本次调用已消耗配额）
                    self._half_open_calls[source_name] = 1
                    return True

                return False

            else:  # HALF_OPEN
                # 检查试探次数
                calls = self._half_open_calls.get(source_name, 0)
                if calls < self._half_open_max_calls:
                    self._half_open_calls[source_name] = calls + 1
                    return True
                return False

    def record_failure(self, source_name: str) -> None:
        """记录失败

        状态转换:
        - Closed: 失败计数 +1，达到阈值则转 Open
        - Half-Open: 试探失败，立即转 Open
        - Open: 无操作（已经是熔断状态）

        Args:
            source_name: 数据源名称
        """
        with self._lock:
            state = self._get_state(source_name)

            if state == CircuitState.CLOSED:
                # 失败计数 +1
                count = self._failure_counts.get(source_name, 0) + 1
                self._failure_counts[source_name] = count
                self._last_failure_time[source_name] = time.time()

                # 达到阈值，熔断
                if count >= self._failure_threshold:
                    self._states[source_name] = CircuitState.OPEN
                    # 发送熔断事件
                    Events.data_source_failed.send(
                        self,
                        source=source_name,
                        error=f"Circuit breaker opened after {count} failures",
                    )

            elif state == CircuitState.HALF_OPEN:
                # 试探失败，立即熔断
                self._states[source_name] = CircuitState.OPEN
                self._last_failure_time[source_name] = time.time()
                self._half_open_calls[source_name] = 0
                # 发送熔断事件
                Events.data_source_failed.send(
                    self,
                    source=source_name,
                    error="Circuit breaker reopened after half-open probe failure",
                )

            # Open 状态无需操作

    def record_success(self, source_name: str) -> None:
        """记录成功

        状态转换:
        - Closed: 重置失败计数
        - Half-Open: 试探成功，转 Closed
        - Open: 无操作（不应该有成功，但防御性编程）

        Args:
            source_name: 数据源名称
        """
        with self._lock:
            state = self._get_state(source_name)

            if state == CircuitState.CLOSED:
                # 重置失败计数
                self._failure_counts[source_name] = 0

            elif state == CircuitState.HALF_OPEN:
                # 试探成功，恢复正常
                self._states[source_name] = CircuitState.CLOSED
                self._failure_counts[source_name] = 0
                self._half_open_calls[source_name] = 0
                # 发送恢复事件
                Events.data_source_recovered.send(
                    self,
                    source=source_name,
                )

    def get_state(self, source_name: str) -> CircuitState:
        """获取数据源的熔断状态（线程安全）"""
        with self._lock:
            return self._get_state(source_name)

    def _get_state(self, source_name: str) -> CircuitState:
        """获取数据源的熔断状态（内部方法，不加锁）"""
        return self._states.get(source_name, CircuitState.CLOSED)

    def get_failure_count(self, source_name: str) -> int:
        """获取失败次数"""
        with self._lock:
            return self._failure_counts.get(source_name, 0)

    def reset(self, source_name: str) -> None:
        """重置数据源的熔断状态"""
        with self._lock:
            self._failure_counts[source_name] = 0
            self._last_failure_time.pop(source_name, None)
            self._states[source_name] = CircuitState.CLOSED
            self._half_open_calls[source_name] = 0

    def reset_all(self) -> None:
        """重置所有数据源的熔断状态"""
        with self._lock:
            self._failure_counts.clear()
            self._last_failure_time.clear()
            self._states.clear()
            self._half_open_calls.clear()
