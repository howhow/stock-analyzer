"""
计时器工具
"""

import time
from contextlib import contextmanager
from typing import Generator


@contextmanager
def timer(name: str = "operation") -> Generator[dict, None, None]:
    """
    计时上下文管理器

    Usage:
        with timer("analysis") as t:
            # do something
            pass
        print(f"Elapsed: {t['elapsed']:.2f}ms")

    Args:
        name: 操作名称

    Yields:
        包含耗时信息的字典
    """
    result = {"name": name, "elapsed": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        result["elapsed"] = elapsed_ms


class Timer:
    """
    计时器类

    Usage:
        t = Timer()
        t.start()
        # do something
        elapsed = t.stop()
    """

    def __init__(self, name: str = "timer"):
        self.name = name
        self._start: float | None = None
        self._elapsed: float = 0.0

    def start(self) -> "Timer":
        """开始计时"""
        self._start = time.perf_counter()
        return self

    def stop(self) -> float:
        """停止计时并返回耗时(ms)"""
        if self._start is None:
            raise RuntimeError("Timer not started")
        self._elapsed = (time.perf_counter() - self._start) * 1000
        self._start = None
        return self._elapsed

    @property
    def elapsed(self) -> float:
        """获取耗时(ms)"""
        return self._elapsed
