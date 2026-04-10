import pytest

"""
工具函数测试
"""

from datetime import date

from app.utils.validators import (
    sanitize_input,
    validate_date_range,
    validate_stock_code,
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


def test_sanitize_input_empty():
    """测试空输入"""
    assert sanitize_input("") == ""
    assert sanitize_input(None) == ""


def test_is_valid_json():
    """测试JSON有效性检查"""
    from app.utils.validators import is_valid_json

    assert is_valid_json({"key": "value"}) is True
    assert is_valid_json([1, 2, 3]) is True
    assert is_valid_json("string") is True
    assert is_valid_json(123) is True


def test_is_valid_json_invalid():
    """测试无效JSON"""
    from app.utils.validators import is_valid_json

    # 包含无法序列化的对象
    class Unserializable:
        pass

    assert is_valid_json(Unserializable()) is False


def test_validate_date_range_defaults():
    """测试日期范围默认值"""
    # 测试 end_date 默认为今天
    start, end = validate_date_range(date(2023, 1, 1), None)
    assert start == date(2023, 1, 1)
    assert end == date.today()

    # 测试 start_date 默认为一年前
    start, end = validate_date_range(None, date(2024, 6, 15))
    assert start == date(2023, 6, 15)
    assert end == date(2024, 6, 15)


def test_validate_date_range_string():
    """测试字符串日期转换"""
    start, end = validate_date_range("2024-01-01", "2024-12-31")
    assert start == date(2024, 1, 1)
    assert end == date(2024, 12, 31)
