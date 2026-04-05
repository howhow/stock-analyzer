"""
Logger补充测试 - 提升覆盖率
"""

import pytest
from unittest.mock import patch, MagicMock

from app.utils.logger import get_logger


class TestLoggerMore:
    """Logger补充测试"""

    def test_logger_info(self):
        """测试logger info方法"""
        logger = get_logger("test_info")
        logger.info("test message", key="value")

    def test_logger_debug(self):
        """测试logger debug方法"""
        logger = get_logger("test_debug")
        logger.debug("debug message")

    def test_logger_warning(self):
        """测试logger warning方法"""
        logger = get_logger("test_warning")
        logger.warning("warning message")

    def test_logger_error(self):
        """测试logger error方法"""
        logger = get_logger("test_error")
        logger.error("error message")

    def test_logger_with_exception(self):
        """测试logger记录异常"""
        logger = get_logger("test_exception")
        try:
            raise ValueError("test error")
        except Exception as e:
            logger.error("caught exception", error=str(e))

    def test_mask_sensitive_data(self):
        """测试脱敏敏感数据"""
        from app.utils.logger import mask_sensitive_data

        data = {
            "password": "secret123",
            "token": "abc123def456ghi789",
            "name": "test",
        }

        result = mask_sensitive_data(data, ["password", "token"])

        # 密码应该被脱敏（保留前后4位）
        assert "***" in result["password"]
        # token应该被脱敏
        assert "***" in result["token"]
        # name不应该被脱敏
        assert result["name"] == "test"
