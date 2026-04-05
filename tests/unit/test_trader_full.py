"""Trader Analyzer完整测试 - 简化版"""

import pytest
from app.analysis.trader import Trader


class TestTraderFull:
    """交易者分析完整测试"""

    def test_init(self):
        """测试初始化"""
        trader = Trader()
        assert trader is not None

    def test_analyzer_name(self):
        """测试分析器名称"""
        trader = Trader()
        assert trader.__class__.__name__ == "Trader"
