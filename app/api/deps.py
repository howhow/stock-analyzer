"""
依赖注入

集成安全认证和限流
"""

from typing import Annotated

from fastapi import Depends

from app.core.limiter import check_rate_limit, get_rate_limiter
from app.core.security import (
    get_current_user,
    get_current_user_optional,
    require_role,
)


# ============ 用户依赖 ============

CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalUser = Annotated[dict | None, Depends(get_current_user_optional)]


# ============ 限流依赖 ============


async def get_rate_limit_info(
    rate_info: dict = Depends(lambda: check_rate_limit(endpoint="analyze")),
) -> dict:
    """获取限流信息"""
    return rate_info


RateLimitInfo = Annotated[dict, Depends(get_rate_limit_info)]


# ============ 角色权限依赖 ============


def RequireRole(role: str):
    """角色权限依赖工厂"""
    return Annotated[dict, Depends(require_role(role))]


# ============ 缓存和数据库依赖 ============


async def get_cache() -> None:
    """获取缓存客户端（待实现）"""
    return None


async def get_db() -> None:
    """获取数据库会话（待实现）"""
    return None


CacheClient = Annotated[object, Depends(get_cache)]
DbSession = Annotated[object, Depends(get_db)]
