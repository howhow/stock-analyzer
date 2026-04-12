"""JWT 认证模块"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import InvalidTokenError as JWTInvalidTokenError
from jwt.exceptions import ExpiredSignatureError

from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)

# 配置
JWT_SECRET_KEY = settings.app_secret_key
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7


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
        except ExpiredSignatureError as e:
            logger.warning("token_expired", error=str(e))
            raise TokenExpiredError("Token has expired")
        except JWTInvalidTokenError as e:
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
