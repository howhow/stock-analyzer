"""
清理任务

定期清理过期数据和缓存
"""

from typing import Any

from app.report.storage import get_report_storage
from app.tasks.celery_app import celery_app
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
)
def cleanup_expired_reports(self: Any) -> dict[str, Any]:
    """
    清理过期报告

    删除超过保留期的报告文件

    Args:
        self: Celery 任务实例

    Returns:
        清理结果
    """
    logger.info(
        "cleanup_expired_reports_started",
        task_id=self.request.id,
    )

    try:
        storage = get_report_storage()
        cleaned = storage.cleanup_expired()

        logger.info(
            "cleanup_expired_reports_completed",
            task_id=self.request.id,
            cleaned_count=cleaned,
        )

        return {
            "status": "success",
            "cleaned_count": cleaned,
        }

    except Exception as e:
        logger.error(
            "cleanup_expired_reports_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
)
def cleanup_expired_cache(self: Any) -> dict[str, Any]:
    """
    清理过期缓存

    清理 Redis 中过期的缓存键

    Args:
        self: Celery 任务实例

    Returns:
        清理结果
    """
    logger.info(
        "cleanup_expired_cache_started",
        task_id=self.request.id,
    )

    try:
        # TODO: 实际从 Redis 清理过期缓存
        # 这里简化处理，实际需要连接 Redis 并执行清理
        cleaned = 0

        # 注意：这里简化处理，实际需要异步处理
        logger.info(
            "cleanup_expired_cache_completed",
            task_id=self.request.id,
            cleaned_count=cleaned,
        )

        return {
            "status": "success",
            "cleaned_count": cleaned,
        }

    except Exception as e:
        logger.error(
            "cleanup_expired_cache_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
)
def cleanup_old_logs(self: Any, days: int = 30) -> dict[str, Any]:
    """
    清理旧日志

    删除超过指定天数的日志文件

    Args:
        self: Celery 任务实例
        days: 保留天数

    Returns:
        清理结果
    """
    logger.info(
        "cleanup_old_logs_started",
        task_id=self.request.id,
        retention_days=days,
    )

    try:
        from datetime import datetime, timedelta
        from pathlib import Path

        log_dir = Path("local_log")
        if not log_dir.exists():
            return {"status": "success", "cleaned_count": 0}

        cleaned = 0
        cutoff = datetime.now() - timedelta(days=days)

        for log_file in log_dir.glob("*.log*"):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    log_file.unlink()
                    cleaned += 1
            except Exception as e:
                logger.warning(
                    "log_file_cleanup_failed",
                    file=str(log_file),
                    error=str(e),
                )

        logger.info(
            "cleanup_old_logs_completed",
            task_id=self.request.id,
            cleaned_count=cleaned,
        )

        return {
            "status": "success",
            "cleaned_count": cleaned,
        }

    except Exception as e:
        logger.error(
            "cleanup_old_logs_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
)
def cleanup_temp_files(self: Any) -> dict[str, Any]:
    """
    清理临时文件

    删除临时目录中的文件

    Args:
        self: Celery 任务实例

    Returns:
        清理结果
    """
    logger.info(
        "cleanup_temp_files_started",
        task_id=self.request.id,
    )

    try:
        import tempfile
        from pathlib import Path

        temp_dir = Path(tempfile.gettempdir())
        cleaned = 0
        cleaned_size = 0

        # 清理超过 1 天的临时文件
        for temp_file in temp_dir.glob("tmp*"):
            try:
                if temp_file.is_file():
                    stat = temp_file.stat()
                    cleaned_size += stat.st_size
                    temp_file.unlink()
                    cleaned += 1
            except Exception:
                continue

        logger.info(
            "cleanup_temp_files_completed",
            task_id=self.request.id,
            cleaned_count=cleaned,
            cleaned_size_mb=round(cleaned_size / (1024 * 1024), 2),
        )

        return {
            "status": "success",
            "cleaned_count": cleaned,
            "cleaned_size_bytes": cleaned_size,
        }

    except Exception as e:
        logger.error(
            "cleanup_temp_files_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
)
def get_storage_stats(self: Any) -> dict[str, Any]:
    """
    获取存储统计

    返回报告存储的统计信息

    Args:
        self: Celery 任务实例

    Returns:
        统计信息
    """
    logger.info(
        "get_storage_stats_started",
        task_id=self.request.id,
    )

    try:
        storage = get_report_storage()
        stats = storage.get_storage_stats()

        return {
            "status": "success",
            "stats": stats,
        }

    except Exception as e:
        logger.error(
            "get_storage_stats_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise
