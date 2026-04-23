"""
安全模块完整测试

目标覆盖率: ≥ 90%
当前覆盖率: 72%
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import (
    APIKeyManager,
    DataEncryptor,
    JWTManager,
    get_api_key_user,
    get_current_user,
    get_current_user_optional,
    get_jwt_user,
    hash_password,
    require_role,
    verify_password,
)


class TestPasswordHashing:
    """密码加密测试"""

    def test_hash_password(self):
        """测试密码加密"""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """测试密码验证 - 正确"""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试密码验证 - 错误"""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False


class TestDataEncryptor:
    """数据加密器测试"""

    def test_encrypt_decrypt_with_auto_key(self):
        """测试自动密钥加密解密"""
        encryptor = DataEncryptor()

        data = "sensitive_data_123"
        encrypted = encryptor.encrypt(data)

        assert encrypted != data

        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == data

    def test_encrypt_decrypt_with_string_key(self):
        """测试字符串密钥加密解密"""
        # 使用有效的 Fernet 密钥（44字符，32字节url-safe base64编码）
        key = "JvctrTpe1ewPDI__whf0gantgifUR8IWX_mUWKWNCQ8="
        encryptor = DataEncryptor(key=key)

        data = "sensitive_data_123"
        encrypted = encryptor.encrypt(data)

        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == data


class TestAPIKeyManager:
    """API Key 管理器测试"""

    def test_generate_api_key(self):
        """测试生成 API Key"""
        api_key = APIKeyManager.generate_api_key()

        assert api_key.startswith("sk_")
        assert len(api_key) > 35

    def test_generate_api_key_with_prefix(self):
        """测试生成带前缀的 API Key"""
        api_key = APIKeyManager.generate_api_key(prefix="pk")

        assert api_key.startswith("pk_")

    def test_validate_api_key_format_valid(self):
        """测试验证 API Key 格式 - 有效"""
        api_key = "sk_" + "a" * 43  # 43 个字符
        assert APIKeyManager.validate_api_key_format(api_key) is True

    def test_validate_api_key_format_invalid_no_underscore(self):
        """测试验证 API Key 格式 - 无下划线"""
        api_key = "invalidkey123456789012345678901234567890"
        assert APIKeyManager.validate_api_key_format(api_key) is False

    def test_validate_api_key_format_invalid_too_short(self):
        """测试验证 API Key 格式 - 太短"""
        api_key = "sk_short"
        assert APIKeyManager.validate_api_key_format(api_key) is False

    def test_validate_api_key_format_invalid_empty(self):
        """测试验证 API Key 格式 - 空"""
        assert APIKeyManager.validate_api_key_format("") is False
        assert APIKeyManager.validate_api_key_format(None) is False


class TestJWTManager:
    """JWT 管理器测试"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        token = JWTManager.create_access_token(
            user_id="user123",
            role="user",
        )

        assert token is not None
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """测试创建带过期时间的访问令牌"""
        expires_delta = timedelta(hours=2)
        token = JWTManager.create_access_token(
            user_id="user123",
            role="user",
            expires_delta=expires_delta,
        )

        assert token is not None

    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        token = JWTManager.create_refresh_token(user_id="user123")

        assert token is not None

    def test_verify_token_success(self):
        """测试验证令牌成功"""
        # 创建令牌
        token = JWTManager.create_access_token(
            user_id="user123",
            role="user",
        )

        # 验证令牌
        payload = JWTManager.verify_token(token, token_type="access")

        assert payload["sub"] == "user123"
        assert payload["role"] == "user"

    def test_verify_token_invalid(self):
        """测试验证无效令牌"""
        from app.core.exceptions import InvalidTokenError

        with pytest.raises(InvalidTokenError):
            JWTManager.verify_token("invalid_token", token_type="access")


class TestGetApiKeyUser:
    """API Key 用户获取测试"""

    @pytest.mark.asyncio
    async def test_get_api_key_user_valid(self):
        """测试获取 API Key 用户 - 有效"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/analyze"

        # 使用有效的 API Key 格式
        api_key = "sk_" + "a" * 43

        # 直接传入 api_key 参数，不依赖 API_KEY_HEADER
        result = await get_api_key_user(request=request, api_key=api_key)

        assert result is not None
        assert result["auth_type"] == "api_key"

    @pytest.mark.asyncio
    async def test_get_api_key_user_invalid_format(self):
        """测试获取 API Key 用户 - 无效格式"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/analyze"

        api_key = "invalid_key"

        with pytest.raises(HTTPException) as exc_info:
            await get_api_key_user(request=request, api_key=api_key)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_api_key_user_none(self):
        """测试获取 API Key 用户 - None"""
        request = Mock(spec=Request)

        result = await get_api_key_user(request=request, api_key=None)

        assert result is None


class TestGetJwtUser:
    """JWT 用户获取测试"""

    @pytest.mark.asyncio
    async def test_get_jwt_user_valid(self):
        """测试获取 JWT 用户 - 有效"""
        # 创建令牌
        token = JWTManager.create_access_token(user_id="user123", role="user")

        credentials = Mock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = token

        result = await get_jwt_user(credentials)

        assert result is not None
        assert result["user_id"] == "user123"
        assert result["auth_type"] == "jwt"

    @pytest.mark.asyncio
    async def test_get_jwt_user_none(self):
        """测试获取 JWT 用户 - None"""
        result = await get_jwt_user(None)

        assert result is None


class TestGetCurrentUser:
    """当前用户获取测试"""

    @pytest.mark.asyncio
    async def test_get_current_user_with_api_key(self):
        """测试获取当前用户 - API Key"""
        api_key_user = {
            "user_id": "api_user",
            "role": "service",
            "auth_type": "api_key",
        }

        result = await get_current_user(api_key_user=api_key_user, jwt_user=None)

        assert result == api_key_user

    @pytest.mark.asyncio
    async def test_get_current_user_with_jwt(self):
        """测试获取当前用户 - JWT"""
        jwt_user = {"user_id": "jwt_user", "role": "user", "auth_type": "jwt"}

        result = await get_current_user(api_key_user=None, jwt_user=jwt_user)

        assert result == jwt_user

    @pytest.mark.asyncio
    async def test_get_current_user_not_authenticated(self):
        """测试获取当前用户 - 未认证"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(api_key_user=None, jwt_user=None)

        assert exc_info.value.status_code == 401


class TestGetCurrentUserOptional:
    """可选当前用户获取测试"""

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_user(self):
        """测试获取可选当前用户 - 有用户"""
        user = {"user_id": "user123", "role": "user"}

        result = await get_current_user_optional(api_key_user=user, jwt_user=None)

        assert result == user

    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_user(self):
        """测试获取可选当前用户 - 无用户"""
        result = await get_current_user_optional(api_key_user=None, jwt_user=None)

        assert result is None


class TestRequireRole:
    """角色权限测试"""

    @pytest.mark.asyncio
    async def test_require_role_success(self):
        """测试角色权限检查 - 通过"""
        role_checker = require_role("user")

        user = {"user_id": "user123", "role": "pro"}

        result = await role_checker(current_user=user)

        assert result == user

    @pytest.mark.asyncio
    async def test_require_role_permission_denied(self):
        """测试角色权限检查 - 权限不足"""
        role_checker = require_role("admin")

        user = {"user_id": "user123", "role": "user"}

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user=user)

        assert exc_info.value.status_code == 403


# 运行测试
if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=app.core.security", "--cov-report=term-missing"]
    )
