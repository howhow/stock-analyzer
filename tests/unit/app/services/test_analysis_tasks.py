"""
分析任务测试

测试异步分析任务。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tasks.analysis_tasks import _batch_analyze_logic

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_celery_task():
    """创建模拟 Celery 任务实例"""
    task = MagicMock()
    task.request.id = "task_001"
    task.request.retries = 0
    task.max_retries = 3
    return task


# ============================================================
# batch_analyze
# ============================================================


class TestBatchAnalyze:
    """测试批量分析任务"""

    @patch("app.tasks.analysis_tasks.async_analyze")
    def test_batch_analyze_success(self, mock_async, mock_celery_task):
        """测试批量分析成功"""
        mock_result = MagicMock()
        mock_result.id = "sub_task_001"
        mock_async.delay.return_value = mock_result

        result = _batch_analyze_logic(mock_celery_task, ["600519.SH", "000001.SZ"])

        assert result["status"] == "success"
        assert result["total"] == 2
        assert result["success"] == 2
        assert result["failed"] == 0
        assert len(result["results"]) == 2

    @patch("app.tasks.analysis_tasks.async_analyze")
    def test_batch_analyze_partial_failure(self, mock_async, mock_celery_task):
        """测试部分失败"""
        mock_async.delay.side_effect = [MagicMock(id="sub_001"), Exception("Error")]

        result = _batch_analyze_logic(mock_celery_task, ["600519.SH", "000001.SZ"])

        assert result["status"] == "partial"
        assert result["total"] == 2
        assert result["success"] == 1
        assert result["failed"] == 1
        assert len(result["errors"]) == 1

    @patch("app.tasks.analysis_tasks.async_analyze")
    def test_batch_analyze_empty_list(self, mock_async, mock_celery_task):
        """测试空列表"""
        result = _batch_analyze_logic(mock_celery_task, [])

        assert result["status"] == "success"
        assert result["total"] == 0
        assert result["success"] == 0
        assert result["failed"] == 0

    @patch("app.tasks.analysis_tasks.async_analyze")
    def test_batch_analyze_all_failure(self, mock_async, mock_celery_task):
        """测试全部失败"""
        mock_async.delay.side_effect = Exception("Error")

        result = _batch_analyze_logic(mock_celery_task, ["600519.SH"])

        assert result["status"] == "partial"
        assert result["total"] == 1
        assert result["success"] == 0
        assert result["failed"] == 1
