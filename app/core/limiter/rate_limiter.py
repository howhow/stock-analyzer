"""限流器管理模块"""

from typing import Any, Callable

from fastapi import HTTPException, Request, status

from app.core.limiter.sliding_window import SlidingWindowLimiter
from app.core.limiter.tiers import RATE_LIMITS, UserTier
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
        tier_limits = RATE_LIMITS.get(tier, RATE_LIMITS[UserTier.FREE])
        max_requests, window_seconds = tier_limits.get(endpoint, (10, 60))
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
            "enterprise": UserTier.ENTERPRISE,
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
    user = getattr(request.state, "user", None)

    if user is None:
        user_id = "anonymous"
        tier = UserTier.FREE
    else:
        user_id = user.get("user_id", "anonymous")
        role = user.get("role", "guest")
        tier = get_rate_limiter().get_tier_from_role(role)

    allowed, remaining, reset_time = await get_rate_limiter().check_limit(
        user_id, tier, endpoint
    )

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

    async def rate_limit_checker(request: Request) -> dict[str, Any]:
        return await check_rate_limit(request, endpoint)

    return rate_limit_checker  # type: ignore


async def rate_limit_middleware(request: Request, call_next: Callable[..., Any]) -> Any:
    """
    限流中间件

    自动添加限流响应头
    """
    response = await call_next(request)

    if hasattr(request.state, "rate_limit_remaining"):
        response.headers["X-RateLimit-Remaining"] = str(
            request.state.rate_limit_remaining
        )

    if hasattr(request.state, "rate_limit_reset"):
        response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)

    return response
