"""
安全模块

实现API Key + JWT双认证方案
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

import bcrypt
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)

# ============ 配置 ============

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
JWT_BEARER = HTTPBearer(auto_error=False)

JWT_SECRET_KEY = settings.app_secret_key
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7


# ============ 密码加密 ============


def hash_password(password: str) -> str:
    """
    使用bcrypt加密密码

    Args:
        password: 明文密码

    Returns:
        加密后的密码哈希
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        是否匹配
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ============ 敏感数据加密 ============


class DataEncryptor:
    """
    敏感数据加密器

    使用Fernet对称加密
    """

    def __init__(self, key: str | bytes | None = None):
        """
        初始化加密器

        Args:
            key: 加密密钥（None则自动生成）
        """
        if key is None:
            self._fernet = Fernet(Fernet.generate_key())
        elif isinstance(key, str):
            self._fernet = Fernet(key.encode("utf-8"))
        else:
            self._fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """
        加密数据

        Args:
            data: 明文数据

        Returns:
            加密后的数据（Base64编码）
        """
        encrypted = self._fernet.encrypt(data.encode("utf-8"))
        return encrypted.decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据

        Args:
            encrypted_data: 加密数据

        Returns:
            明文数据
        """
        decrypted = self._fernet.decrypt(encrypted_data.encode("utf-8"))
        return decrypted.decode("utf-8")


# ============ API Key 认证 ============


class APIKeyManager:
    """
    API Key管理器

    用于服务间调用的认证
    """

    @staticmethod
    def generate_api_key(prefix: str = "sk") -> str:
        """
        生成API Key

        Args:
            prefix: 前缀

        Returns:
            API Key
        """
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"

    @staticmethod
    def validate_api_key_format(api_key: str) -> bool:
        """
        验证API Key格式

        Args:
            api_key: API Key

        Returns:
            是否有效
        """
        if not api_key:
            return False
        parts = api_key.split("_", 1)  # 只分割第一个下划线
        return len(parts) == 2 and len(parts[1]) >= 32


# ============ JWT 认证 ============


class JWTManager:
    """
    JWT Token管理器

    用于用户认证
    """

    @staticmethod
    def create_access_token(
        user_id: str,
        role: str = "user",
        expires_delta: timedelta | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> str:
        """
        创建访问令牌

        Args:
            user_id: 用户ID
            role: 用户角色
            expires_delta: 过期时间增量
            extra_data: 额外数据

        Returns:
            JWT令牌
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        expire = datetime.now(timezone.utc) + expires_delta

        payload = {
            "sub": user_id,
            "role": role,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }

        if extra_data:
            payload.update(extra_data)

        return str(jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM))

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """
        创建刷新令牌

        Args:
            user_id: 用户ID

        Returns:
            JWT刷新令牌
        """
        expire = datetime.now(timezone.utc) + timedelta(
            days=JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        }

        return str(jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM))

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        """
        解码令牌

        Args:
            token: JWT令牌

        Returns:
            解码后的payload

        Raises:
            InvalidTokenError: 无效令牌
            TokenExpiredError: 令牌过期
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return dict(payload)
        except jwt.ExpiredSignatureError as e:
            logger.warning("token_expired", error=str(e))
            raise TokenExpiredError("Token has expired")
        except JWTError as e:
            logger.warning("invalid_token", error=str(e))
            raise InvalidTokenError("Invalid token")

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict[str, Any]:
        """
        验证令牌

        Args:
            token: JWT令牌
            token_type: 令牌类型（access/refresh）

        Returns:
            解码后的payload

        Raises:
            InvalidTokenError: 无效令牌
        """
        payload = JWTManager.decode_token(token)

        if payload.get("type") != token_type:
            raise InvalidTokenError(f"Expected {token_type} token")

        return payload


# ============ FastAPI 依赖注入 ============


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

    TODO: 生产环境需要实现以下功能：
    1. 从数据库查询 API Key 是否存在
    2. 验证 API Key 是否过期
    3. 验证 API Key 的权限范围
    4. 记录 API Key 使用日志到数据库
    """
    if api_key is None:
        return None

    # ⚠️ 开发模式：仅验证格式，不验证真实性
    # TODO: 从数据库验证API Key
    if APIKeyManager.validate_api_key_format(api_key):
        # 记录API Key使用
        logger.info(
            "api_key_auth_dev_mode",
            api_key_prefix=api_key[:10],
            path=request.url.path,
            warning="Development mode: API Key not validated against database",
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
    # 优先使用API Key
    if api_key_user is not None:
        return api_key_user

    # 其次使用JWT
    if jwt_user is not None:
        return jwt_user

    # 未认证
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

        # 角色层级: admin > pro > user > guest
        role_hierarchy = {
            "admin": 100,
            "pro": 50,
            "user": 10,
            "guest": 0,
            "service": 100,  # 服务账号
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
