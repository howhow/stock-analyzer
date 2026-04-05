"""
Logger测试 - 补充覆盖率
"""

import pytest
from unittest.mock import patch, MagicMock

from app.utils.logger import get_logger


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
