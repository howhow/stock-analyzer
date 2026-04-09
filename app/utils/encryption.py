"""
加密工具模块

提供API Key加密存储功能
"""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.exceptions import StockAnalyzerError


class EncryptionError(StockAnalyzerError):
    """加密错误"""

    pass


class EncryptionManager:
    """
    加密管理器

    使用Fernet (AES-128-CBC) 对称加密
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
                else self._derive_key(encryption_key)
            )
        except Exception as e:
            raise EncryptionError(f"Invalid encryption key: {e}") from e

    def _derive_key(self, password: str) -> bytes:
        """
        从密码派生密钥

        Args:
            password: 密码字符串

        Returns:
            Base64编码的Fernet密钥
        """
        # 使用固定的salt（生产环境应使用随机salt并存储）
        salt = b"stock_analyzer_encryption_salt_v1"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串

        Args:
            plaintext: 明文字符串

        Returns:
            加密后的字符串（base64编码）

        Raises:
            EncryptionError: 加密失败
        """
        if not plaintext:
            return ""

        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}") from e

    def decrypt(self, encrypted_text: str) -> str:
        """
        解密字符串

        Args:
            encrypted_text: 加密字符串（base64编码）

        Returns:
            解密后的明文

        Raises:
            EncryptionError: 解密失败
        """
        if not encrypted_text:
            return ""

        try:
            decrypted = self.fernet.decrypt(encrypted_text.encode())
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
        EncryptionError: 未配置ENCRYPTION_KEY
    """
    global _encryption_manager

    if _encryption_manager is None:
        from app.core.config import settings

        if not settings.ENCRYPTION_KEY:
            raise EncryptionError("ENCRYPTION_KEY not configured in environment")

        _encryption_manager = EncryptionManager(settings.ENCRYPTION_KEY)

    return _encryption_manager
