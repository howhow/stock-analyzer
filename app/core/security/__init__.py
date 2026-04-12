"""安全模块

实现API Key + JWT双认证方案
"""

from app.core.security.api_key import APIKeyManager
from app.core.security.dependencies import (
    get_api_key_user,
    get_current_user,
    get_current_user_optional,
    get_jwt_user,
    require_role,
)
from app.core.security.encryption import DataEncryptor
from app.core.security.jwt_auth import JWTManager
from app.core.security.password import hash_password, verify_password

__all__ = [
    # 密码加密
    "hash_password",
    "verify_password",
    # 数据加密
    "DataEncryptor",
    # API Key
    "APIKeyManager",
    # JWT
    "JWTManager",
    # FastAPI 依赖
    "get_api_key_user",
    "get_jwt_user",
    "get_current_user",
    "get_current_user_optional",
    "require_role",
]
