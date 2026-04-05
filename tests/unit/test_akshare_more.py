"""
AKShareClient补充测试 - 提升覆盖率
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import pandas as pd

from app.data.akshare_client import AKShareClient


class TestAKShareClientMore:
    """AKShareClient补充测试"""

    def test_client_init(self):
        """测试初始化"""
        client = AKShareClient()
        assert client is not None
        assert client.name == "akshare"

    def test_client_with_custom_params(self):
        """测试自定义参数初始化"""
        client = AKShareClient(timeout=30, max_retries=5)
        assert client is not None
        assert client.max_retries == 5

    def test_normalize_stock_code(self):
        """测试标准化股票代码"""
        client = AKShareClient()

        # 测试各种格式
        result = client._normalize_stock_code("000001.SZ")
        assert result == "000001.SZ"

        result = client._normalize_stock_code("600000.SH")
        assert result == "600000.SH"

    def test_split_code(self):
        """测试分割股票代码"""
        client = AKShareClient()

        code, market = client._split_code("000001.SZ")
        assert code == "000001"
        assert market == "SZ"

        code, market = client._split_code("600000.SH")
        assert code == "600000"
        assert market == "SH"
