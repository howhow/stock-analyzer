"""
缓存管理

实现多级缓存架构
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class CacheManager:
    """
    多级缓存管理器

    L1: 本地缓存（进程内）
    L2: Redis缓存（分布式）
    """

    def __init__(
        self,
        redis_url: str = "",
        max_local_size: int = 1000,
        default_ttl: int = 1800,
    ):
        """
        初始化缓存管理器

        Args:
            redis_url: Redis连接URL
            max_local_size: 本地缓存最大条目数
            default_ttl: 默认TTL（秒）
        """
        self.redis_url = redis_url or settings.redis_url
        self.max_local_size = max_local_size
        self.default_ttl = default_ttl

        # L1: 本地缓存
        self._local_cache: dict[str, tuple[Any, float]] = {}
        self._local_lock = asyncio.Lock()

        # L2: Redis客户端
        self._redis_client: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis | None:
        """获取Redis客户端"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # 测试连接
                await self._redis_client.ping()
                logger.info("redis_connected", url=self.redis_url)
            except Exception as e:
                logger.warning("redis_connection_failed", error=str(e))
                self._redis_client = None

        return self._redis_client

    async def get(self, key: str) -> Any | None:
        """
        获取缓存值

        先查L1，再查L2

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        # L1: 本地缓存
        local_value = await self._get_local(key)
        if local_value is not None:
            return local_value

        # L2: Redis缓存
        redis_value = await self._get_redis_cache(key)
        if redis_value is not None:
            # 回填L1
            await self._set_local(key, redis_value, ttl=60)
            return redis_value

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        设置缓存值

        同时写入L1和L2

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        ttl = ttl or self.default_ttl

        # 写入L1
        await self._set_local(key, value, ttl=min(ttl, 60))

        # 写入L2
        await self._set_redis_cache(key, value, ttl)

        return True

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        # 删除L1
        async with self._local_lock:
            self._local_cache.pop(key, None)

        # 删除L2
        redis_client = await self._get_redis()
        if redis_client:
            try:
                await redis_client.delete(key)
            except Exception as e:
                logger.warning("redis_delete_failed", key=key, error=str(e))

        return True

    async def _get_local(self, key: str) -> Any | None:
        """获取本地缓存"""
        async with self._local_lock:
            if key not in self._local_cache:
                return None

            value, expire_time = self._local_cache[key]

            # 检查过期
            if datetime.now().timestamp() > expire_time:
                del self._local_cache[key]
                return None

            return value

    async def _set_local(self, key: str, value: Any, ttl: int) -> None:
        """设置本地缓存"""
        async with self._local_lock:
            # LRU淘汰
            if len(self._local_cache) >= self.max_local_size:
                # 删除最早的一半
                keys = list(self._local_cache.keys())
                for old_key in keys[: len(keys) // 2]:
                    del self._local_cache[old_key]

            expire_time = datetime.now().timestamp() + ttl
            self._local_cache[key] = (value, expire_time)

    async def _get_redis_cache(self, key: str) -> Any | None:
        """获取Redis缓存"""
        redis_client = await self._get_redis()
        if not redis_client:
            return None

        try:
            value = await redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning("redis_get_failed", key=key, error=str(e))

        return None

    async def _set_redis_cache(self, key: str, value: Any, ttl: int) -> bool:
        """设置Redis缓存"""
        redis_client = await self._get_redis()
        if not redis_client:
            return False

        try:
            # 添加随机偏移防止雪崩
            actual_ttl = ttl + random.randint(-int(ttl * 0.1), int(ttl * 0.1))
            await redis_client.setex(key, actual_ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.warning("redis_set_failed", key=key, error=str(e))
            return False

    def make_key(self, prefix: str, *args: Any) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            *args: 参数

        Returns:
            缓存键
        """
        parts = [prefix] + [str(arg) for arg in args]
        return ":".join(parts)

    async def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        async with self._local_lock:
            local_size = len(self._local_cache)

        redis_client = await self._get_redis()
        redis_info = {}
        if redis_client:
            try:
                info = await redis_client.info("memory")
                redis_info = {
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected": True,
                }
            except Exception:
                redis_info = {"connected": False}

        return {
            "local_cache_size": local_size,
            "max_local_size": self.max_local_size,
            "redis": redis_info,
        }

    async def clear_local(self) -> None:
        """清空本地缓存"""
        async with self._local_lock:
            self._local_cache.clear()

    async def close(self) -> None:
        """关闭连接"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
