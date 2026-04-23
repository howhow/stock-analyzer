"""
Celery 配置测试
"""

import pytest

from app.tasks.celery_app import celery_app, get_celery_app


class TestCeleryApp:
    """Celery 应用测试"""

    def test_celery_app_created(self) -> None:
        """测试 Celery 应用创建"""
        assert celery_app is not None
        assert celery_app.main == "stock_analyzer"

    def test_get_celery_app(self) -> None:
        """测试获取 Celery 应用"""
        app = get_celery_app()
        assert app is celery_app

    def test_celery_config(self) -> None:
        """测试 Celery 配置"""
        config = celery_app.conf

        assert config.task_serializer == "json"
        assert config.result_serializer == "json"
        assert config.timezone == "Asia/Shanghai"
        assert config.task_time_limit == 300
        assert config.task_max_retries == 3

    def test_beat_schedule(self) -> None:
        """测试定时任务配置"""
        schedule = celery_app.conf.beat_schedule

        assert "cleanup-expired-reports" in schedule
        assert "cleanup-expired-cache" in schedule
        assert "execute-subscriptions-morning" in schedule
        assert "execute-subscriptions-afternoon" in schedule
        assert "process-dead-letter-queue" in schedule

    def test_included_modules(self) -> None:
        """测试包含的模块"""
        includes = celery_app.conf.include

        assert "app.tasks.analysis_tasks" in includes
        assert "app.tasks.subscribe_tasks" in includes
        assert "app.tasks.cleanup_tasks" in includes
        assert "app.tasks.dead_letter" in includes
