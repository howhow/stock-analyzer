"""滑动窗口限流器模块"""

import time

import redis.asyncio as redis

from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class SlidingWindowLimiter:
    """
    滑动窗口限流器

    使用Redis实现分布式限流
    """

    def __init__(self, redis_client: redis.Redis | None = None):
        """
        初始化限流器

        Args:
            redis_client: Redis客户端
        """
        self._redis = redis_client
        self._local_cache: dict[str, list[float]] = {}

    async def _get_redis(self) -> redis.Redis | None:
        """获取Redis客户端"""
        if self._redis is None:
            try:
                self._redis = redis.from_url(  # type: ignore[no-untyped-call]
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except Exception as e:
                logger.warning("redis_connection_failed", error=str(e))
                self._redis = None

        return self._redis

    async def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        检查是否允许请求（滑动窗口算法）

        Args:
            key: 限流键
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (是否允许, 剩余次数, 重置时间)
        """
        redis_client = await self._get_redis()

        if redis_client is not None:
            return await self._check_with_redis(
                redis_client, key, max_requests, window_seconds
            )
        else:
            return self._check_with_local(key, max_requests, window_seconds)

    async def _check_with_redis(
        self,
        redis_client: redis.Redis,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """使用Redis检查限流"""
        now = time.time()
        window_start = now - window_seconds

        # 使用Lua脚本保证原子性
        lua_script = """
        local key = KEYS[1]
        local window_start = tonumber(ARGV[1])
        local now = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])
        local window_seconds = tonumber(ARGV[4])

        -- 移除过期的请求
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

        -- 获取当前窗口内的请求数
        local current = redis.call('ZCARD', key)

        if current < max_requests then
            -- 添加新请求
            redis.call('ZADD', key, now, now .. '-' .. math.random())
            redis.call('EXPIRE', key, window_seconds)
            return {1, max_requests - current - 1, window_seconds}
        else
            -- 计算重置时间
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local reset_time = math.ceil(oldest[2] + window_seconds - now)
            return {0, 0, reset_time}
        end
        """

        try:
            result = await redis_client.eval(  # type: ignore[misc]
                lua_script,
                1,
                key,  # type: ignore[arg-type]
                window_start,  # type: ignore[arg-type]
                now,  # type: ignore[arg-type]
                max_requests,  # type: ignore[arg-type]
                window_seconds,  # type: ignore[arg-type]
            )

            allowed = bool(result[0])
            remaining = int(result[1])
            reset_time = int(result[2])

            return allowed, remaining, reset_time

        except Exception as e:
            logger.error(
                "rate_limit_check_failed_fallback_to_local",
                error=str(e),
                key=key,
            )
            return self._check_with_local(key, max_requests, window_seconds)

    def _check_with_local(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """使用本地缓存检查限流（降级方案）"""
        now = time.time()
        window_start = now - window_seconds

        if key not in self._local_cache:
            self._local_cache[key] = []

        self._local_cache[key] = [
            ts for ts in self._local_cache[key] if ts > window_start
        ]

        current = len(self._local_cache[key])

        if current < max_requests:
            self._local_cache[key].append(now)
            return True, max_requests - current - 1, window_seconds
        else:
            oldest = min(self._local_cache[key])
            reset_time = int(oldest + window_seconds - now)
            return False, 0, reset_time
