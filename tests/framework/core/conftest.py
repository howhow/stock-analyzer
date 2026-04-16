"""
Framework Core 测试配置

为 framework/core 模块测试提供隔离的 fixture。
避免依赖 app 模块。
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


# 在导入 framework 模块前 Mock 掉依赖
@pytest.fixture(scope="session", autouse=True)
def mock_framework_dependencies():
    """Mock framework 模块的外部依赖"""
    
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.cache_ttl_daily = 1800
    mock_settings.circuit_breaker_threshold = 3
    
    # Mock logger
    mock_logger = MagicMock()
    
    with patch.dict(
        sys.modules,
        {
            "config": MagicMock(settings=mock_settings),
            "config.settings": mock_settings,
            "app.utils.logger": MagicMock(get_logger=MagicMock(return_value=mock_logger)),
            "app.core.cache": MagicMock(),
        },
    ):
        yield mock_settings, mock_logger
