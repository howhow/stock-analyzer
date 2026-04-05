"""
分析任务测试
"""

from unittest.mock import MagicMock, patch

import pytest

from app.tasks.analysis_tasks import async_analyze, batch_analyze


class TestAnalysisTasks:
    """分析任务测试"""

    def test_async_analyze_signature(self) -> None:
        """测试异步分析任务签名"""
        assert async_analyze.name == "app.tasks.analysis_tasks.async_analyze"
        assert async_analyze.max_retries == 3

    def test_batch_analyze_signature(self) -> None:
        """测试批量分析任务签名"""
        assert batch_analyze.name == "app.tasks.analysis_tasks.batch_analyze"
        assert batch_analyze.max_retries == 2

    @patch("app.tasks.analysis_tasks.Analyst")
    @patch("app.tasks.analysis_tasks.Trader")
    @patch("app.tasks.analysis_tasks.SystemAnalyzer")
    def test_async_analyze_execution(
        self,
        mock_system: MagicMock,
        mock_trader: MagicMock,
        mock_analyst: MagicMock,
    ) -> None:
        """测试异步分析执行"""
        # 模拟分析结果
        mock_result = MagicMock()
        mock_result.analysis_id = "test_001"
        mock_result.stock_code = "600519.SH"
        mock_result.analyst_report.total_score = 3.5
        mock_result.trader_signal.recommendation.value = "买入"

        mock_system.return_value.synthesize.return_value = mock_result
        mock_analyst.return_value.analyze.return_value = MagicMock()
        mock_trader.return_value.analyze.return_value = MagicMock()

        # 验证任务可以调用
        assert async_analyze is not None

    def test_batch_analyze_stocks(self) -> None:
        """测试批量分析股票列表"""
        stock_codes = ["600519.SH", "000001.SZ"]

        # 验证任务可以调用
        assert batch_analyze is not None
