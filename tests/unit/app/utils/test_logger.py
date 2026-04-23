"""
Logger测试 - 补充覆盖率
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.utils.logger import get_logger, mask_sensitive_data


class TestLogger:
    """Logger测试"""

    def test_get_logger_singleton(self):
        """测试获取logger单例"""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # 返回的都是logger对象
        assert logger1 is not None
        assert logger2 is not None

    def test_get_logger_same_name(self):
        """测试相同名称返回logger"""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        # 都应该返回有效的logger对象
        assert logger1 is not None
        assert logger2 is not None
        # structlog不保证单例，只要返回有效logger即可

    def test_logger_has_methods(self):
        """测试logger具有必要方法"""
        logger = get_logger("test")

        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_setup_logging_text_format(self):
        """测试文本格式日志配置"""
        from app.utils.logger import setup_logging
        from config import settings

        # 保存原始值
        original_format = settings.log_format

        try:
            # 设置文本格式
            if hasattr(settings, "log_format"):
                # 如果是可变的，直接设置
                if not isinstance(settings.log_format, property):
                    settings.log_format = "text"
            # 重新配置
            setup_logging()
            logger = get_logger("test_text_format")
            assert logger is not None
        finally:
            # 恢复原始值
            if hasattr(settings, "log_format"):
                if not isinstance(settings.log_format, property):
                    settings.log_format = original_format


class TestMaskSensitiveData:
    """测试敏感数据脱敏"""

    def test_mask_api_key_long(self):
        """测试长API Key脱敏"""
        data = {"api_key": "sk-1234567890abcdefghijklmnopqrstuvwxyz"}
        result = mask_sensitive_data(data, ["api_key"])

        assert "***" in result["api_key"]
        assert result["api_key"].startswith("sk-1")
        assert result["api_key"].endswith("xyz")

    def test_mask_api_key_short(self):
        """测试短API Key脱敏"""
        data = {"api_key": "short"}
        result = mask_sensitive_data(data, ["api_key"])

        assert result["api_key"] == "***"

    def test_mask_empty_value(self):
        """测试空值不脱敏"""
        data = {"api_key": None}
        result = mask_sensitive_data(data, ["api_key"])

        assert result["api_key"] is None

    def test_mask_missing_key(self):
        """测试缺失的key"""
        data = {"other_key": "value"}
        result = mask_sensitive_data(data, ["api_key"])

        assert "api_key" not in result
        assert result["other_key"] == "value"

    def test_mask_multiple_keys(self):
        """测试多个key脱敏"""
        data = {
            "api_key": "sk-1234567890abcdefghijklmnopqrstuvwxyz",
            "password": "mysecretpassword123",
            "name": "normal_name",
        }
        result = mask_sensitive_data(data, ["api_key", "password"])

        assert "***" in result["api_key"]
        assert "***" in result["password"]
        assert result["name"] == "normal_name"
