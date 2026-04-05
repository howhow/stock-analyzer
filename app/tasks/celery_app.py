"""
Celery 应用配置

异步任务队列配置
"""

from celery import Celery
from celery.schedules import crontab

from config import settings

# 创建 Celery 应用
celery_app = Celery(
    "stock_analyzer",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.analysis_tasks",
        "app.tasks.subscribe_tasks",
        "app.tasks.cleanup_tasks",
        "app.tasks.dead_letter",
    ],
)

# Celery 配置
celery_app.conf.update(
    # 任务结果配置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    # 任务执行配置
    task_acks_late=True,  # 任务完成后才确认
    task_reject_on_worker_lost=True,  # Worker 丢失时拒绝任务
    task_time_limit=300,  # 硬超时 5 分钟
    task_soft_time_limit=270,  # 软超时 4.5 分钟
    # 重试配置
    task_default_retry_delay=60,  # 重试延迟 60 秒
    task_max_retries=3,  # 最大重试 3 次
    # 结果配置
    result_expires=3600,  # 结果过期时间 1 小时
    # Worker 配置
    worker_prefetch_multiplier=1,  # 每次只取一个任务
    worker_concurrency=4,  # 并发数
    # 限流配置
    worker_disable_rate_limits=False,
    task_default_rate_limit="10/m",  # 默认限流 10 次/分钟
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    # 每天凌晨 2 点清理过期报告
    "cleanup-expired-reports": {
        "task": "app.tasks.cleanup_tasks.cleanup_expired_reports",
        "schedule": crontab(hour=2, minute=0),
    },
    # 每小时清理过期缓存
    "cleanup-expired-cache": {
        "task": "app.tasks.cleanup_tasks.cleanup_expired_cache",
        "schedule": crontab(minute=0),
    },
    # 每天 9:15 执行订阅分析
    "execute-subscriptions-morning": {
        "task": "app.tasks.subscribe_tasks.execute_subscriptions",
        "schedule": crontab(hour=9, minute=15),
    },
    # 每天 15:05 执行订阅分析
    "execute-subscriptions-afternoon": {
        "task": "app.tasks.subscribe_tasks.execute_subscriptions",
        "schedule": crontab(hour=15, minute=5),
    },
    # 每小时检查死信队列
    "process-dead-letter-queue": {
        "task": "app.tasks.dead_letter.process_dead_letter_queue",
        "schedule": crontab(minute=30),
    },
}


def get_celery_app() -> Celery:
    """获取 Celery 应用实例"""
    return celery_app
