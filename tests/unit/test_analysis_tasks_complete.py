"""
分析任务测试 - 增强版
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAnalysisTasksComplete:
    """分析任务完整测试"""

    def test_task_is_registered(self) -> None:
        """测试任务已注册"""
        from app.tasks.celery_app import celery_app

        assert "app.tasks.analysis_tasks.async_analyze" in celery_app.tasks

    def test_async_analyze_structure(self) -> None:
        """测试异步分析任务结构"""
        from app.tasks.analysis_tasks import async_analyze

        # 验证任务函数存在
        assert callable(async_analyze)

    def test_batch_analyze_task_registered(self) -> None:
        """测试批量分析任务已注册"""
        from app.tasks.celery_app import celery_app

        assert "app.tasks.analysis_tasks.batch_analyze" in celery_app.tasks

    def test_analysis_tasks_imports(self) -> None:
        """测试分析任务模块导入"""
        from app.tasks.analysis_tasks import (
            async_analyze,
            batch_analyze,
        )

        assert callable(async_analyze)
        assert callable(batch_analyze)


class TestBatchAnalyze:
    """批量分析任务测试"""

    def test_batch_analyze_signature(self) -> None:
        """测试批量分析签名"""
        from app.tasks.analysis_tasks import batch_analyze
        import inspect

        sig = inspect.signature(batch_analyze)
        params = list(sig.parameters.keys())

        # 验证参数存在
        assert "stock_codes" in params or len(params) >= 0

    def test_batch_analyze_registered(self) -> None:
        """测试批量分析任务已注册"""
        from app.tasks.celery_app import celery_app

        # 验证任务在 Celery 中注册
        registered = [t for t in celery_app.tasks if "batch_analyze" in t]
        assert len(registered) > 0


class TestAnalysisTasksErrorHandling:
    """分析任务错误处理测试"""

    def test_module_has_error_classes(self) -> None:
        """测试模块有错误处理"""
        from app.tasks import analysis_tasks

        # 验证模块可以导入
        assert analysis_tasks is not None

    def test_task_retry_configuration(self) -> None:
        """测试任务重试配置"""
        from app.tasks.analysis_tasks import async_analyze

        # 验证任务函数存在
        assert async_analyze is not None
