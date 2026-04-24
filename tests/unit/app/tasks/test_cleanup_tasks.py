"""
清理任务测试
"""

from unittest.mock import MagicMock, patch

import pytest

from app.tasks.cleanup_tasks import (
    cleanup_expired_cache,
    cleanup_expired_reports,
    cleanup_old_logs,
    cleanup_temp_files,
    get_storage_stats,
)


class TestCleanupExpiredReports:
    """测试清理过期报告任务"""

    def test_task_is_registered(self) -> None:
        """测试任务已注册"""
        from app.tasks.celery_app import celery_app

        # 验证任务已注册
        assert "app.tasks.cleanup_tasks.cleanup_expired_reports" in celery_app.tasks

    @patch("app.tasks.cleanup_tasks.get_report_storage")
    def test_cleanup_expired_reports_success(self, mock_get_storage: MagicMock) -> None:
        """测试成功清理过期报告"""
        # Mock storage
        mock_storage = MagicMock()
        mock_storage.cleanup_expired = MagicMock(return_value=5)
        mock_get_storage.return_value = mock_storage

        # 执行任务
        result = cleanup_expired_reports()

        assert result["status"] == "success"
        assert result["cleaned_count"] == 5

    @patch("app.tasks.cleanup_tasks.get_report_storage")
    def test_cleanup_expired_reports_error(self, mock_get_storage: MagicMock) -> None:
        """测试清理过期报告错误"""
        mock_get_storage.side_effect = Exception("Storage error")

        # 执行任务应该抛出异常
        with pytest.raises(Exception):
            cleanup_expired_reports()


class TestCleanupExpiredCache:
    """测试清理过期缓存任务"""

    def test_task_is_registered(self) -> None:
        """测试任务已注册"""
        from app.tasks.celery_app import celery_app

        assert "app.tasks.cleanup_tasks.cleanup_expired_cache" in celery_app.tasks

    def test_cleanup_expired_cache_success(self) -> None:
        """测试成功清理过期缓存"""
        result = cleanup_expired_cache()

        assert result["status"] == "success"
        assert "cleaned_count" in result


class TestCleanupOldLogs:
    """测试清理旧日志任务"""

    def test_task_is_registered(self) -> None:
        """测试任务已注册"""
        from app.tasks.celery_app import celery_app

        assert "app.tasks.cleanup_tasks.cleanup_old_logs" in celery_app.tasks

    def test_cleanup_old_logs_no_dir(self) -> None:
        """测试日志目录不存在"""
        with patch("pathlib.Path.exists", return_value=False):
            result = cleanup_old_logs(days=30)

            assert result["status"] == "success"
            assert result["cleaned_count"] == 0

    def test_cleanup_old_logs_success(self) -> None:
        """测试清理日志文件成功"""
        # 直接调用函数测试基本功能
        result = cleanup_old_logs(days=30)

        assert result["status"] == "success"
        assert "cleaned_count" in result


class TestCleanupTempFiles:
    """测试清理临时文件任务"""

    def test_task_is_registered(self) -> None:
        """测试任务已注册"""
        from app.tasks.celery_app import celery_app

        assert "app.tasks.cleanup_tasks.cleanup_temp_files" in celery_app.tasks

    def test_cleanup_temp_files_success(self) -> None:
        """测试成功清理临时文件"""
        with patch("tempfile.gettempdir", return_value="/tmp"):
            with patch("pathlib.Path.glob", return_value=[]):
                result = cleanup_temp_files()

                assert result["status"] == "success"
                assert "cleaned_count" in result


class TestGetStorageStats:
    """测试获取存储统计任务"""

    def test_task_is_registered(self) -> None:
        """测试任务已注册"""
        from app.tasks.celery_app import celery_app

        assert "app.tasks.cleanup_tasks.get_storage_stats" in celery_app.tasks

    @patch("app.tasks.cleanup_tasks.get_report_storage")
    def test_get_storage_stats_success(self, mock_get_storage: MagicMock) -> None:
        """测试成功获取存储统计"""
        mock_storage = MagicMock()
        mock_storage.get_storage_stats = MagicMock(
            return_value={
                "total_reports": 10,
                "total_size_bytes": 1024,
            }
        )
        mock_get_storage.return_value = mock_storage

        result = get_storage_stats()

        assert result["status"] == "success"
        assert result["stats"]["total_reports"] == 10

    @patch("app.tasks.cleanup_tasks.get_report_storage")
    def test_get_storage_stats_error(self, mock_get_storage: MagicMock) -> None:
        """测试获取存储统计错误"""
        mock_get_storage.side_effect = Exception("Storage error")

        with pytest.raises(Exception):
            get_storage_stats()
