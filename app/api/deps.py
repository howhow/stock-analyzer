"""
依赖注入
"""

from typing import Annotated

from fastapi import Depends


# TODO: 实现具体的依赖注入
async def get_current_user():
    """获取当前用户"""
    # TODO: 从 JWT 或 API Key 获取用户
    return {"user_id": "anonymous", "role": "guest"}


async def get_cache():
    """获取缓存客户端"""
    # TODO: 返回 Redis 客户端
    return None


async def get_db():
    """获取数据库会话"""
    # TODO: 返回数据库会话
    return None


# 类型别名
CurrentUser = Annotated[dict, Depends(get_current_user)]
CacheClient = Annotated[object, Depends(get_cache)]
DbSession = Annotated[object, Depends(get_db)]
