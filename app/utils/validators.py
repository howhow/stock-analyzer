"""
验证器工具
"""

import re
from datetime import date, datetime
from typing import Any


def validate_stock_code(code: str) -> str:
    """
    验证股票代码格式

    Args:
        code: 股票代码

    Returns:
        验证后的股票代码（大写）

    Raises:
        ValueError: 股票代码格式无效
    """
    if not code:
        raise ValueError("stock code cannot be empty")

    # 支持格式: 600519.SH, 000001.SZ, 00700.HK (港股可能是5位或6位)
    pattern = r"^\d{5,6}\.(SH|SZ|HK)$"
    if not re.match(pattern, code.upper()):
        raise ValueError(f"invalid stock code format: {code}, expected: XXXXXX.SH/SZ/HK")

    return code.upper()


def validate_date_range(
    start_date: date | str | None,
    end_date: date | str | None,
) -> tuple[date, date]:
    """
    验证日期范围

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        (start_date, end_date) 元组

    Raises:
        ValueError: 日期范围无效
    """
    # 转换字符串为日期
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 默认值
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = date(end_date.year - 1, end_date.month, end_date.day)

    # 验证范围
    if start_date > end_date:
        raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")

    return start_date, end_date


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """
    清理输入字符串

    移除危险字符，限制长度

    Args:
        value: 输入字符串
        max_length: 最大长度

    Returns:
        清理后的字符串
    """
    if not value:
        return ""

    # 移除控制字符
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", value)

    # 限制长度
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()


def is_valid_json(value: Any) -> bool:
    """
    检查是否为有效的 JSON 值

    Args:
        value: 待检查的值

    Returns:
        是否为有效的 JSON 值
    """
    import json

    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False
