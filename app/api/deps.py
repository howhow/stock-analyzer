"""
依赖注入

集成安全认证和限流
"""

from typing import Annotated, Any

from fastapi import Depends, Request

from app.core.limiter import check_rate_limit
from app.core.security import (
    get_current_user,
    get_current_user_optional,
    require_role,
)

# ============ 用户依赖 ============

CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
OptionalUser = Annotated[dict[str, Any] | None, Depends(get_current_user_optional)]


# ============ 限流依赖 ============


async def get_rate_limit_info(
    request: Request,
) -> dict[str, Any]:
    """获取限流信息"""
    return await check_rate_limit(request, endpoint="analyze")


RateLimitInfo = Annotated[dict[str, Any], Depends(get_rate_limit_info)]


# ============ 角色权限依赖 ============


def RequireRole(role: str) -> Any:
    """角色权限依赖工厂"""
    return Annotated[dict[str, Any], Depends(require_role(role))]


# ============ 缓存和数据库依赖 ============


async def get_cache() -> None:
    """获取缓存客户端（待实现）"""
    return None


async def get_db() -> None:
    """获取数据库会话（待实现）"""
    return None


CacheClient = Annotated[object, Depends(get_cache)]
DbSession = Annotated[object, Depends(get_db)]
