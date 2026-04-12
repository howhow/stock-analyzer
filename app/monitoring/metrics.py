"""
监控指标占位模块

prometheus-client 已移除，监控指标功能待重构。
"""


# 占位符 - 避免导入错误
def record_http_request(*args, **kwargs) -> None:
    """占位符"""
    pass


def record_analysis(*args, **kwargs) -> None:
    """占位符"""
    pass


def record_cache_hit(*args, **kwargs) -> None:
    """占位符"""
    pass


def record_cache_miss(*args, **kwargs) -> None:
    """占位符"""
    pass


def get_metrics() -> bytes:
    """占位符"""
    return b""


__all__ = [
    "record_http_request",
    "record_analysis",
    "record_cache_hit",
    "record_cache_miss",
    "get_metrics",
]
