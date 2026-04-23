"""System Analyzer完整测试 - 简化版"""

import pytest

from app.analysis.system import SystemAnalyzer


class TestSystemAnalyzerFull:
    """系统分析器完整测试"""

    def test_init(self):
        """测试初始化"""
        analyzer = SystemAnalyzer()
        assert analyzer is not None

    def test_analyzer_name(self):
        """测试分析器名称"""
        analyzer = SystemAnalyzer()
        assert analyzer.__class__.__name__ == "SystemAnalyzer"
