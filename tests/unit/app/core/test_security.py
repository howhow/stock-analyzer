"""
安全模块测试
"""

from datetime import datetime, timedelta

import pytest

from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security import (
    APIKeyManager,
    DataEncryptor,
    JWTManager,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """密码加密测试"""

    def test_hash_password(self) -> None:
        """测试密码加密"""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_success(self) -> None:
        """测试密码验证成功"""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self) -> None:
        """测试密码验证失败"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False


class TestDataEncryptor:
    """数据加密器测试"""

    def test_encrypt_decrypt(self) -> None:
        """测试加密解密"""
        encryptor = DataEncryptor()
        data = "sensitive_data_123"

        encrypted = encryptor.encrypt(data)
        decrypted = encryptor.decrypt(encrypted)

        assert encrypted != data
        assert decrypted == data

    def test_encrypt_different_results(self) -> None:
        """测试相同数据加密结果不同（Fernet特性）"""
        encryptor = DataEncryptor()
        data = "test_data"

        encrypted1 = encryptor.encrypt(data)
        encrypted2 = encryptor.encrypt(data)

        # Fernet每次加密结果不同（包含时间戳）
        assert encrypted1 != encrypted2

    def test_decrypt_invalid_data(self) -> None:
        """测试解密无效数据"""
        encryptor = DataEncryptor()

        with pytest.raises(Exception):
            encryptor.decrypt("invalid_encrypted_data")


class TestAPIKeyManager:
    """API Key管理器测试"""

    def test_generate_api_key(self) -> None:
        """测试生成API Key"""
        api_key = APIKeyManager.generate_api_key()

        assert api_key.startswith("sk_")
        assert len(api_key) > 35

    def test_generate_api_key_with_prefix(self) -> None:
        """测试自定义前缀"""
        api_key = APIKeyManager.generate_api_key(prefix="pk")

        assert api_key.startswith("pk_")

    def test_validate_api_key_format_valid(self) -> None:
        """测试验证有效API Key格式"""
        api_key = APIKeyManager.generate_api_key()

        assert APIKeyManager.validate_api_key_format(api_key) is True

    def test_validate_api_key_format_invalid(self) -> None:
        """测试验证无效API Key格式"""
        assert APIKeyManager.validate_api_key_format("") is False
        assert APIKeyManager.validate_api_key_format("invalid") is False
        assert APIKeyManager.validate_api_key_format("sk_short") is False

    def test_validate_api_key_format_none(self) -> None:
        """测试验证None"""
        assert APIKeyManager.validate_api_key_format(None) is False


class TestJWTManager:
    """JWT管理器测试"""

    def test_create_access_token(self) -> None:
        """测试创建访问令牌"""
        user_id = "user_123"
        token = JWTManager.create_access_token(user_id)

        assert token is not None
        assert len(token) > 50

    def test_create_access_token_with_role(self) -> None:
        """测试创建带角色的访问令牌"""
        user_id = "user_123"
        role = "admin"
        token = JWTManager.create_access_token(user_id, role=role)

        payload = JWTManager.decode_token(token)
        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "access"

    def test_create_access_token_with_extra_data(self) -> None:
        """测试创建带额外数据的访问令牌"""
        user_id = "user_123"
        extra_data = {"email": "test@example.com", "name": "Test User"}
        token = JWTManager.create_access_token(user_id, extra_data=extra_data)

        payload = JWTManager.decode_token(token)
        assert payload["email"] == "test@example.com"
        assert payload["name"] == "Test User"

    def test_create_refresh_token(self) -> None:
        """测试创建刷新令牌"""
        user_id = "user_123"
        token = JWTManager.create_refresh_token(user_id)

        payload = JWTManager.decode_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_decode_token_valid(self) -> None:
        """测试解码有效令牌"""
        user_id = "user_123"
        token = JWTManager.create_access_token(user_id)

        payload = JWTManager.decode_token(token)

        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_token_invalid(self) -> None:
        """测试解码无效令牌"""
        with pytest.raises(InvalidTokenError):
            JWTManager.decode_token("invalid.token.here")

    def test_verify_token_access(self) -> None:
        """测试验证访问令牌"""
        user_id = "user_123"
        token = JWTManager.create_access_token(user_id)

        payload = JWTManager.verify_token(token, token_type="access")
        assert payload["sub"] == user_id

    def test_verify_token_refresh(self) -> None:
        """测试验证刷新令牌"""
        user_id = "user_123"
        token = JWTManager.create_refresh_token(user_id)

        payload = JWTManager.verify_token(token, token_type="refresh")
        assert payload["sub"] == user_id

    def test_verify_token_type_mismatch(self) -> None:
        """测试令牌类型不匹配"""
        user_id = "user_123"
        access_token = JWTManager.create_access_token(user_id)

        with pytest.raises(InvalidTokenError, match="Expected refresh token"):
            JWTManager.verify_token(access_token, token_type="refresh")

    def test_token_expiration(self) -> None:
        """测试令牌过期"""
        user_id = "user_123"
        # 创建一个立即过期的令牌
        token = JWTManager.create_access_token(
            user_id, expires_delta=timedelta(seconds=-1)
        )

        with pytest.raises((TokenExpiredError, InvalidTokenError)):
            JWTManager.decode_token(token)
