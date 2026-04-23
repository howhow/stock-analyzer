"""
日志工具模块

结构化日志配置，支持脱敏
"""

import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import Processor

from config import settings

# 统一日志目录：local_log/（已被 .gitignore 的 local_* 规则排除）
LOG_DIR = Path("local_log")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging() -> None:
    """
    配置结构化日志

    使用 structlog 实现结构化日志，支持 JSON 格式输出
    日志输出到 local_log/ 目录（已被 .gitignore 排除）
    """
    # 日志级别映射
    log_level = getattr(logging, settings.log_level)

    # 共享处理器
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    # 根据环境选择输出格式
    if settings.log_format == "json":
        # JSON 格式（生产环境）
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # 文本格式（开发环境）
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # 配置 structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 配置标准库 logging — 输出到 local_log/
    log_file = LOG_DIR / "app.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    # 同时输出到控制台
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    logging.basicConfig(
        level=log_level,
        handlers=[file_handler, console_handler],
    )


def get_logger(name: str | None = None) -> Any:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称，通常使用 __name__

    Returns:
        配置好的结构化日志记录器
    """
    return structlog.get_logger(name)


def mask_sensitive_data(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    """
    脱敏敏感数据

    Args:
        data: 原始数据
        keys: 需要脱敏的键名列表

    Returns:
        脱敏后的数据
    """
    result = data.copy()
    for key in keys:
        if key in result and result[key]:
            value = str(result[key])
            if len(value) > 8:
                result[key] = f"{value[:4]}***{value[-4:]}"
            else:
                result[key] = "***"
    return result


# 初始化日志
setup_logging()

# 默认 logger
logger = get_logger(__name__)
