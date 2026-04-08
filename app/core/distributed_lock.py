"""
分布式锁

用于防止缓存击穿
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as redis

from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class DistributedLock:
    """
    分布式锁

    基于Redis实现，支持自动续期
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        key: str,
        timeout: int = 30,
        retry_times: int = 3,
        retry_delay: float = 0.1,
    ):
        """
        初始化分布式锁

        Args:
            redis_client: Redis客户端
            key: 锁的键名
            timeout: 锁超时时间（秒）
            retry_times: 获取锁重试次数
            retry_delay: 重试延迟（秒）
        """
        self._redis = redis_client
        self._key = f"lock:{key}"
        self._timeout = timeout
        self._retry_times = retry_times
        self._retry_delay = retry_delay
        self._token = str(uuid.uuid4())
        self._locked = False

    async def acquire(self) -> bool:
        """
        获取锁

        Returns:
            是否成功获取
        """
        for attempt in range(self._retry_times):
            try:
                # 使用SET NX EX原子操作
                acquired = await self._redis.set(
                    self._key,
                    self._token,
                    nx=True,
                    ex=self._timeout,
                )

                if acquired:
                    self._locked = True
                    logger.debug(
                        "lock_acquired",
                        key=self._key,
                        token=self._token,
                        attempt=attempt + 1,
                    )
                    return True

                # 未获取到锁，等待重试
                if attempt < self._retry_times - 1:
                    await asyncio.sleep(self._retry_delay)

            except Exception as e:
                logger.error(
                    "lock_acquire_error",
                    key=self._key,
                    error=str(e),
                    attempt=attempt + 1,
                )

        logger.warning(
            "lock_acquire_failed",
            key=self._key,
            retry_times=self._retry_times,
        )
        return False

    async def release(self) -> bool:
        """
        释放锁

        Returns:
            是否成功释放
        """
        if not self._locked:
            return False

        try:
            # 使用Lua脚本保证原子性
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = await self._redis.eval(  # type: ignore[misc]
                
                lua_script, 1, self._key, self._token  # type: ignore[arg-type]
            )

            self._locked = False

            if result:
                logger.debug("lock_released", key=self._key, token=self._token)
                return True
            else:
                logger.warning(
                    "lock_release_failed",
                    key=self._key,
                    token=self._token,
                    reason="token_mismatch",
                )
                return False

        except Exception as e:
            logger.error("lock_release_error", key=self._key, error=str(e))
            return False

    async def extend(self, additional_time: int | None = None) -> bool:
        """
        延长锁的持有时间

        Args:
            additional_time: 额外时间（秒），默认为原始timeout

        Returns:
            是否成功延长
        """
        if not self._locked:
            return False

        try:
            # 使用Lua脚本保证原子性
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """

            ttl = additional_time or self._timeout
            result = await self._redis.eval(  # type: ignore[misc]
                
                lua_script, 1, self._key, self._token, ttl  # type: ignore[arg-type]
            )

            if result:
                logger.debug("lock_extended", key=self._key, ttl=ttl)
                return True
            else:
                logger.warning("lock_extend_failed", key=self._key)
                return False

        except Exception as e:
            logger.error("lock_extend_error", key=self._key, error=str(e))
            return False

    @asynccontextmanager
    async def __call__(self) -> AsyncIterator["DistributedLock"]:
        """
        上下文管理器

        用法:
            async with DistributedLock(redis, "my_lock") as lock:
                if lock._locked:
                    # 执行需要加锁的操作
                    pass
        """
        acquired = await self.acquire()
        try:
            yield self
        finally:
            if acquired:
                await self.release()


# 类型别名，用于类型检查
AsyncContextManager = DistributedLock


class DistributedLockManager:
    """
    分布式锁管理器

    提供统一的锁获取和释放接口
    """

    def __init__(self, redis_url: str | None = None):
        """
        初始化锁管理器

        Args:
            redis_url: Redis连接URL
        """
        self._redis_url = redis_url or settings.redis_url
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """获取Redis客户端"""
        if self._redis is None:
            self._redis = redis.from_url(  # type: ignore[no-untyped-call]
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    @asynccontextmanager
    async def lock(
        self,
        key: str,
        timeout: int = 30,
        retry_times: int = 3,
        retry_delay: float = 0.1,
    ) -> AsyncIterator[DistributedLock]:
        """
        获取分布式锁（上下文管理器）

        Args:
            key: 锁的键名
            timeout: 锁超时时间（秒）
            retry_times: 获取锁重试次数
            retry_delay: 重试延迟（秒）

        Yields:
            DistributedLock实例

        Usage:
            async with lock_manager.lock("cache:update:stock_000001") as lock:
                if lock._locked:
                    # 执行需要加锁的操作
                    pass
        """
        redis_client = await self._get_redis()
        lock = DistributedLock(
            redis_client,
            key,
            timeout=timeout,
            retry_times=retry_times,
            retry_delay=retry_delay,
        )

        async with lock() as acquired_lock:
            yield acquired_lock

    async def try_lock(
        self,
        key: str,
        timeout: int = 30,
    ) -> DistributedLock | None:
        """
        尝试获取锁（非阻塞）

        Args:
            key: 锁的键名
            timeout: 锁超时时间（秒）

        Returns:
            锁实例或None
        """
        redis_client = await self._get_redis()
        lock = DistributedLock(
            redis_client,
            key,
            timeout=timeout,
            retry_times=1,
        )

        if await lock.acquire():
            return lock
        return None


# 全局锁管理器实例
_lock_manager: DistributedLockManager | None = None


def get_lock_manager() -> DistributedLockManager:
    """获取全局锁管理器实例"""
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = DistributedLockManager()
    return _lock_manager
