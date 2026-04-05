import pytest

"""
工具函数测试
"""

from datetime import date

from app.utils.validators import (
    validate_stock_code,
    validate_date_range,
    sanitize_input,
)


def test_validate_stock_code_valid():
    """测试有效股票代码"""
    assert validate_stock_code("600519.SH") == "600519.SH"
    assert validate_stock_code("000001.sz") == "000001.SZ"
    assert validate_stock_code("00700.HK") == "00700.HK"


def test_validate_stock_code_invalid():
    """测试无效股票代码"""
    with pytest.raises(ValueError):
        validate_stock_code("")
    with pytest.raises(ValueError):
        validate_stock_code("600519")
    with pytest.raises(ValueError):
        validate_stock_code("INVALID")


def test_validate_date_range():
    """测试日期范围验证"""
    start, end = validate_date_range(
        date(2024, 1, 1),
        date(2024, 12, 31),
    )
    assert start == date(2024, 1, 1)
    assert end == date(2024, 12, 31)


def test_validate_date_range_invalid():
    """测试无效日期范围"""
    with pytest.raises(ValueError):
        validate_date_range(
            date(2024, 12, 31),
            date(2024, 1, 1),
        )


def test_sanitize_input():
    """测试输入清理"""
    assert sanitize_input("  test  ") == "test"
    assert sanitize_input("a" * 2000, max_length=100) == "a" * 100
    assert sanitize_input("test\x00\x01") == "test"
