"""
限流器模块

实现分级限流策略
"""

import time
from enum import Enum
from typing import Any, Callable

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


# ============ 用户等级定义 ============


class UserTier(str, Enum):
    """用户等级"""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    SERVICE = "service"  # 服务账号


# 限流配置（按文档7.1.1节）
RATE_LIMITS: dict[UserTier, dict[str, tuple[int, int]]] = {
    UserTier.FREE: {
        "analyze": (10, 60),  # 10次/分钟
        "batch_analyze": (2, 60),  # 2次/分钟
        "ai_enhanced": (5, 86400),  # 5次/天
    },
    UserTier.PRO: {
        "analyze": (60, 60),  # 60次/分钟
        "batch_analyze": (10, 60),  # 10次/分钟
        "ai_enhanced": (100, 2592000),  # 100次/月
    },
    UserTier.ENTERPRISE: {
        "analyze": (300, 60),  # 300次/分钟
        "batch_analyze": (30, 60),  # 30次/分钟
        "ai_enhanced": (999999, 1),  # 无限制
    },
    UserTier.SERVICE: {
        "analyze": (1000, 60),  # 1000次/分钟
        "batch_analyze": (100, 60),  # 100次/分钟
        "ai_enhanced": (999999, 1),  # 无限制
    },
}


# ============ 滑动窗口限流器 ============


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
            # 安全降级：降级到本地限流，而不是完全放开
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

        # 获取或初始化请求列表
        if key not in self._local_cache:
            self._local_cache[key] = []

        # 移除过期请求
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


# ============ 限流器管理 ============


class RateLimiter:
    """
    限流器管理器

    集成分级限流策略
    """

    def __init__(self) -> None:
        self._limiter = SlidingWindowLimiter()

    async def check_limit(
        self,
        user_id: str,
        tier: UserTier,
        endpoint: str,
    ) -> tuple[bool, int, int]:
        """
        检查限流

        Args:
            user_id: 用户ID
            tier: 用户等级
            endpoint: 端点类型（analyze/batch_analyze/ai_enhanced）

        Returns:
            (是否允许, 剩余次数, 重置时间)
        """
        # 获取该等级的限流配置
        tier_limits = RATE_LIMITS.get(tier, RATE_LIMITS[UserTier.FREE])
        max_requests, window_seconds = tier_limits.get(endpoint, (10, 60))

        # 构建限流键
        key = f"rate_limit:{tier.value}:{user_id}:{endpoint}"

        return await self._limiter.is_allowed(key, max_requests, window_seconds)

    def get_tier_from_role(self, role: str) -> UserTier:
        """
        从角色获取用户等级

        Args:
            role: 用户角色

        Returns:
            用户等级
        """
        role_mapping = {
            "admin": UserTier.ENTERPRISE,
            "enterprise": UserTier.ENTERPRISE,  # 企业用户映射
            "pro": UserTier.PRO,
            "user": UserTier.FREE,
            "guest": UserTier.FREE,
            "service": UserTier.SERVICE,
        }
        return role_mapping.get(role, UserTier.FREE)


# 全局限流器实例
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# ============ FastAPI 依赖注入 ============


async def check_rate_limit(
    request: Request,
    endpoint: str = "analyze",
) -> dict[str, Any]:
    """
    检查限流（FastAPI依赖）

    Args:
        request: 请求对象
        endpoint: 端点类型

    Returns:
        限流信息

    Raises:
        HTTPException: 超过限流
    """
    # 从请求状态获取用户信息
    user = getattr(request.state, "user", None)

    if user is None:
        # 未认证用户使用guest等级
        user_id = "anonymous"
        tier = UserTier.FREE
    else:
        user_id = user.get("user_id", "anonymous")
        role = user.get("role", "guest")
        tier = get_rate_limiter().get_tier_from_role(role)

    # 检查限流
    allowed, remaining, reset_time = await get_rate_limiter().check_limit(
        user_id, tier, endpoint
    )

    # 设置响应头
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset_time

    if not allowed:
        logger.warning(
            "rate_limit_exceeded",
            user_id=user_id,
            tier=tier.value,
            endpoint=endpoint,
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": str(reset_time),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
            },
        )

    return {
        "allowed": allowed,
        "remaining": remaining,
        "reset_time": reset_time,
        "tier": tier.value,
    }


def rate_limit(endpoint: str = "analyze") -> Callable[[Request], dict[str, Any]]:
    """
    限流装饰器

    Args:
        endpoint: 端点类型

    Returns:
        依赖函数
    """

    async def rate_limit_checker(
        request: Request,
    ) -> dict[str, Any]:
        return await check_rate_limit(request, endpoint)

    return rate_limit_checker  # type: ignore


# ============ 中间件 ============


async def rate_limit_middleware(request: Request, call_next: Callable[..., Any]) -> Any:
    """
    限流中间件

    自动添加限流响应头
    """
    # 执行请求
    response = await call_next(request)

    # 添加限流响应头
    if hasattr(request.state, "rate_limit_remaining"):
        response.headers["X-RateLimit-Remaining"] = str(
            request.state.rate_limit_remaining
        )

    if hasattr(request.state, "rate_limit_reset"):
        response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)

    return response
