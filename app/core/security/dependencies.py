"""FastAPI 依赖注入模块"""

from typing import Any, Awaitable, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security.api_key import APIKeyManager
from app.core.security.jwt_auth import JWTManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 安全方案
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
JWT_BEARER = HTTPBearer(auto_error=False)


async def get_api_key_user(
    request: Request,
    api_key: str | None = Depends(API_KEY_HEADER),
) -> dict[str, Any] | None:
    """
    从API Key获取用户信息

    Args:
        request: 请求对象
        api_key: API Key

    Returns:
        用户信息字典

    Raises:
        HTTPException: 认证失败

    ⚠️ 开发模式说明：
    当前版本仅验证 API Key 格式，未实现数据库查询验证。
    这意味着任何格式正确的 API Key 都能通过验证。
    适用场景：仅用于开发和测试环境，不应用于生产环境。
    """
    if api_key is None:
        return None

    if APIKeyManager.validate_api_key_format(api_key):
        logger.info(
            "api_key_auth_dev_mode",
            api_key_prefix=api_key[:10],
            path=request.url.path,
        )
        return {
            "user_id": "api_user",
            "role": "service",
            "auth_type": "api_key",
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )


async def get_jwt_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(JWT_BEARER),
) -> dict[str, Any] | None:
    """
    从JWT获取用户信息

    Args:
        credentials: Bearer凭证

    Returns:
        用户信息字典

    Raises:
        HTTPException: 认证失败
    """
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        payload = JWTManager.verify_token(token, token_type="access")
        logger.info(
            "jwt_auth",
            user_id=payload.get("sub"),
            role=payload.get("role"),
        )
        return {
            "user_id": payload.get("sub"),
            "role": payload.get("role"),
            "auth_type": "jwt",
        }
    except (TokenExpiredError, InvalidTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    api_key_user: dict[str, Any] | None = Depends(get_api_key_user),
    jwt_user: dict[str, Any] | None = Depends(get_jwt_user),
) -> dict[str, Any]:
    """
    获取当前用户（支持API Key和JWT双重认证）

    优先级：API Key > JWT

    Returns:
        用户信息字典

    Raises:
        HTTPException: 未认证
    """
    if api_key_user is not None:
        return api_key_user

    if jwt_user is not None:
        return jwt_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_optional(
    api_key_user: dict[str, Any] | None = Depends(get_api_key_user),
    jwt_user: dict[str, Any] | None = Depends(get_jwt_user),
) -> dict[str, Any] | None:
    """
    获取当前用户（可选认证）

    Returns:
        用户信息字典或None
    """
    return api_key_user or jwt_user


def require_role(required_role: str) -> Callable[..., Awaitable[dict[str, Any]]]:
    """
    角色权限装饰器

    Args:
        required_role: 要求的角色

    Returns:
        依赖函数
    """

    async def role_checker(
        current_user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        user_role = current_user.get("role", "guest")

        role_hierarchy = {
            "admin": 100,
            "pro": 50,
            "user": 10,
            "guest": 0,
            "service": 100,
        }

        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 100):
            logger.warning(
                "permission_denied",
                user_id=current_user.get("user_id"),
                required_role=required_role,
                actual_role=user_role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return current_user

    return role_checker
