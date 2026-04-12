"""
加密工具模块

提供API Key加密存储功能，支持随机salt增强安全性
"""

import base64
import os
import secrets
from typing import Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.exceptions import StockAnalyzerError


class EncryptionError(StockAnalyzerError):
    """加密错误"""

    pass


# 旧版本固定 salt（用于向后兼容）
LEGACY_SALT = b"stock_analyzer_encryption_salt_v1"

# Salt 长度（字节）
SALT_LENGTH = 16

# 加密数据格式版本
ENCRYPTION_VERSION = 2  # v1 = 固定 salt, v2 = 随机 salt


class EncryptionManager:
    """
    加密管理器

    使用Fernet (AES-128-CBC) 对称加密，支持随机salt增强安全性
    """

    def __init__(self, encryption_key: str):
        """
        初始化加密管理器

        Args:
            encryption_key: 加密密钥（base64编码或原始字符串）

        Raises:
            EncryptionError: 密钥无效
        """
        if not encryption_key:
            raise EncryptionError("Encryption key is required")

        try:
            # 尝试直接作为Fernet密钥使用
            self.fernet = Fernet(
                encryption_key.encode()
                if len(encryption_key) == 44
                else self._derive_key(encryption_key, LEGACY_SALT)
            )
            self.encryption_key = encryption_key
        except Exception as e:
            raise EncryptionError(f"Invalid encryption key: {e}") from e

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        从密码和salt派生密钥

        Args:
            password: 密码字符串
            salt: salt字节

        Returns:
            Base64编码的Fernet密钥
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def _generate_salt(self) -> bytes:
        """
        生成随机salt

        Returns:
            随机salt字节
        """
        return secrets.token_bytes(SALT_LENGTH)

    def _encode_encrypted_data(
        self, salt: bytes, encrypted: bytes, version: int = ENCRYPTION_VERSION
    ) -> str:
        """
        编码加密数据（包含salt和版本）

        格式：v{version}:{base64_salt}:{base64_encrypted}

        Args:
            salt: salt字节
            encrypted: 加密数据字节
            version: 加密版本

        Returns:
            编码后的字符串
        """
        salt_b64 = base64.urlsafe_b64encode(salt).decode()
        encrypted_b64 = base64.urlsafe_b64encode(encrypted).decode()
        return f"v{version}:{salt_b64}:{encrypted_b64}"

    def _decode_encrypted_data(self, encoded: str) -> Tuple[bytes, bytes, int]:
        """
        解码加密数据

        Args:
            encoded: 编码的加密数据

        Returns:
            (salt, encrypted_data, version) 元组

        Raises:
            EncryptionError: 格式无效
        """
        # 检查是否是旧格式（无版本前缀）
        if not encoded.startswith("v"):
            # 旧格式，使用固定 salt
            return LEGACY_SALT, encoded.encode(), 1

        try:
            parts = encoded.split(":")
            if len(parts) != 3:
                raise EncryptionError("Invalid encrypted data format")

            version_str, salt_b64, encrypted_b64 = parts
            version = int(version_str[1:])  # 移除 'v' 前缀
            salt = base64.urlsafe_b64decode(salt_b64)
            encrypted = base64.urlsafe_b64decode(encrypted_b64)

            return salt, encrypted, version
        except Exception as e:
            raise EncryptionError(f"Failed to decode encrypted data: {e}") from e

    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串（使用随机salt）

        Args:
            plaintext: 明文字符串

        Returns:
            加密后的字符串（包含salt和版本）

        Raises:
            EncryptionError: 加密失败
        """
        if not plaintext:
            return ""

        try:
            # 生成随机 salt
            salt = self._generate_salt()

            # 使用随机 salt 派生密钥
            key = self._derive_key(self.encryption_key, salt)
            fernet = Fernet(key)

            # 加密
            encrypted = fernet.encrypt(plaintext.encode())

            # 编码（包含 salt 和版本）
            return self._encode_encrypted_data(salt, encrypted)
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}") from e

    def decrypt(self, encrypted_text: str) -> str:
        """
        解密字符串（支持新旧格式）

        Args:
            encrypted_text: 加密字符串

        Returns:
            解密后的明文

        Raises:
            EncryptionError: 解密失败
        """
        if not encrypted_text:
            return ""

        try:
            # 解码加密数据
            salt, encrypted, version = self._decode_encrypted_data(encrypted_text)

            # 根据 salt 派生密钥
            key = self._derive_key(self.encryption_key, salt)
            fernet = Fernet(key)

            # 解密
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}") from e


def generate_encryption_key() -> str:
    """
    生成新的加密密钥

    Returns:
        Base64编码的Fernet密钥
    """
    return Fernet.generate_key().decode()


# 全局加密管理器实例（延迟初始化）
_encryption_manager: EncryptionManager | None = None


def get_encryption_manager() -> EncryptionManager:
    """
    获取全局加密管理器实例

    Returns:
        EncryptionManager实例

    Raises:
        EncryptionError: 未配置encryption_key
    """
    global _encryption_manager

    if _encryption_manager is None:
        from app.core.config import settings

        if not settings.encryption_key:
            raise EncryptionError("encryption_key not configured in environment")

        _encryption_manager = EncryptionManager(settings.encryption_key)

    return _encryption_manager
