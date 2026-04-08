"""
订阅任务导入测试 - 简单有效
"""

import pytest


class TestTasksImport:
    """任务模块导入测试"""
    
    def test_import_analysis_tasks(self):
        """测试导入分析任务"""
        from app.tasks import analysis_tasks
        assert analysis_tasks is not None
    
    def test_import_cleanup_tasks(self):
        """测试导入清理任务"""
        from app.tasks import cleanup_tasks
        assert cleanup_tasks is not None
    
    def test_import_subscribe_tasks(self):
        """测试导入订阅任务"""
        from app.tasks import subscribe_tasks
        assert subscribe_tasks is not None
    
    def test_import_dead_letter(self):
        """测试导入死信队列"""
        from app.tasks import dead_letter
        assert dead_letter is not None
    
    def test_analysis_task_exists(self):
        """测试分析任务存在"""
        from app.tasks.analysis_tasks import async_analyze
        assert async_analyze is not None
    
    def test_cleanup_task_exists(self):
        """测试清理任务存在"""
        from app.tasks.cleanup_tasks import cleanup_expired_reports
        assert cleanup_expired_reports is not None
    
    def test_subscribe_task_exists(self):
        """测试订阅任务存在"""
        from app.tasks.subscribe_tasks import execute_subscriptions
        assert execute_subscriptions is not None
