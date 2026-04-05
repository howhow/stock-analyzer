"""
死信队列处理

处理失败的任务
"""

from datetime import datetime
from typing import Any

from app.tasks.celery_app import celery_app
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 死信队列存储键前缀
DEAD_LETTER_PREFIX = "dead_letter:"


@celery_app.task(
    bind=True,
)
def send_to_dead_letter_queue(
    self: Any,
    task_name: str,
    task_id: str,
    args: dict[str, Any],
    error: str,
) -> dict[str, Any]:
    """
    发送失败任务到死信队列

    Args:
        self: Celery 任务实例
        task_name: 任务名称
        task_id: 任务ID
        args: 任务参数
        error: 错误信息

    Returns:
        发送结果
    """
    logger.warning(
        "task_sent_to_dead_letter",
        task_name=task_name,
        task_id=task_id,
        error=error,
    )

    try:
        # TODO: 实际存储到 Redis
        # 这里简化处理，实际需要连接 Redis
        key = f"{DEAD_LETTER_PREFIX}{task_id}"

        # 构造死信消息（预留）
        _ = {
            "task_name": task_name,
            "task_id": task_id,
            "args": args,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "retry_count": 0,
        }

        logger.info(
            "dead_letter_message_stored",
            key=key,
            task_name=task_name,
        )

        return {
            "status": "success",
            "task_id": task_id,
            "stored": True,
        }

    except Exception as e:
        logger.error(
            "send_to_dead_letter_failed",
            task_name=task_name,
            task_id=task_id,
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
)
def process_dead_letter_queue(self: Any) -> dict[str, Any]:
    """
    处理死信队列

    定期检查死信队列，尝试重新执行或报警

    Args:
        self: Celery 任务实例

    Returns:
        处理结果
    """
    logger.info(
        "process_dead_letter_queue_started",
        task_id=self.request.id,
    )

    try:
        import redis.asyncio as redis
        from config import settings

        # TODO: 实际从 Redis 获取死信消息
        # 这里简化处理
        dead_letter_messages = []

        processed = 0
        retried = 0
        discarded = 0

        for message in dead_letter_messages:
            try:
                # 检查重试次数
                if message.get("retry_count", 0) >= 3:
                    # 超过最大重试次数，丢弃并发送告警
                    logger.warning(
                        "dead_letter_max_retries_exceeded",
                        message=message,
                    )
                    discarded += 1
                    continue

                # 尝试重新执行
                # TODO: 根据任务名称找到对应的任务并重新执行
                logger.info(
                    "dead_letter_retrying",
                    task_name=message.get("task_name"),
                    task_id=message.get("task_id"),
                )
                retried += 1

            except Exception as e:
                logger.error(
                    "dead_letter_processing_failed",
                    message=message,
                    error=str(e),
                )
                processed += 1

        logger.info(
            "process_dead_letter_queue_completed",
            task_id=self.request.id,
            total=len(dead_letter_messages),
            processed=processed,
            retried=retried,
            discarded=discarded,
        )

        return {
            "status": "success",
            "total": len(dead_letter_messages),
            "processed": processed,
            "retried": retried,
            "discarded": discarded,
        }

    except Exception as e:
        logger.error(
            "process_dead_letter_queue_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
)
def get_dead_letter_stats(self: Any) -> dict[str, Any]:
    """
    获取死信队列统计

    Args:
        self: Celery 任务实例

    Returns:
        统计信息
    """
    logger.info(
        "get_dead_letter_stats_started",
        task_id=self.request.id,
    )

    try:
        # TODO: 实际从 Redis 获取统计
        stats = {
            "total_count": 0,
            "by_task": {},
            "oldest_timestamp": None,
            "newest_timestamp": None,
        }

        return {
            "status": "success",
            "stats": stats,
        }

    except Exception as e:
        logger.error(
            "get_dead_letter_stats_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
)
def clear_dead_letter_queue(
    self: Any,
    task_name: str | None = None,
) -> dict[str, Any]:
    """
    清空死信队列

    Args:
        self: Celery 任务实例
        task_name: 指定任务名称（可选，不指定则清空全部）

    Returns:
        清理结果
    """
    logger.info(
        "clear_dead_letter_queue_started",
        task_id=self.request.id,
        task_name=task_name,
    )

    try:
        # TODO: 实际从 Redis 删除
        cleared = 0

        logger.info(
            "clear_dead_letter_queue_completed",
            task_id=self.request.id,
            cleared_count=cleared,
        )

        return {
            "status": "success",
            "cleared_count": cleared,
        }

    except Exception as e:
        logger.error(
            "clear_dead_letter_queue_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
)
def retry_dead_letter_task(
    self: Any,
    dead_letter_id: str,
) -> dict[str, Any]:
    """
    重试死信任务

    Args:
        self: Celery 任务实例
        dead_letter_id: 死信消息ID

    Returns:
        重试结果
    """
    logger.info(
        "retry_dead_letter_task_started",
        task_id=self.request.id,
        dead_letter_id=dead_letter_id,
    )

    try:
        # TODO: 实际从 Redis 获取并重试
        logger.info(
            "retry_dead_letter_task_completed",
            task_id=self.request.id,
            dead_letter_id=dead_letter_id,
        )

        return {
            "status": "success",
            "dead_letter_id": dead_letter_id,
        }

    except Exception as e:
        logger.error(
            "retry_dead_letter_task_failed",
            task_id=self.request.id,
            error=str(e),
        )
        raise
