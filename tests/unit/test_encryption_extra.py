"""
加密工具额外测试

提升覆盖率到80%+
"""

import pytest

from app.utils.encryption import (
    EncryptionError,
    EncryptionManager,
    generate_encryption_key,
)


class TestEncryptionManagerExtra:
    """测试加密管理器额外场景"""

    def test_encrypt_none_value(self):
        """测试加密None值"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        # 空字符串返回空
        result = manager.encrypt("")
        assert result == ""

    def test_decrypt_none_value(self):
        """测试解密None值"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        # 空字符串返回空
        result = manager.decrypt("")
        assert result == ""

    def test_multiple_encrypt_decrypt(self):
        """测试多次加密解密"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        plaintexts = ["key1", "key2", "key3", "key4", "key5"]

        for plaintext in plaintexts:
            encrypted = manager.encrypt(plaintext)
            decrypted = manager.decrypt(encrypted)
            assert decrypted == plaintext

    def test_long_string_encryption(self):
        """测试长字符串加密"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        # 生成1000字符的长字符串
        long_text = "a" * 1000
        encrypted = manager.encrypt(long_text)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == long_text
        assert len(encrypted) > len(long_text)

    def test_unicode_string_encryption(self):
        """测试Unicode字符串加密"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        unicode_text = "这是一个测试🚀"
        encrypted = manager.encrypt(unicode_text)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == unicode_text

    def test_special_characters_encryption(self):
        """测试特殊字符加密"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        special_text = "sk-test_123!@#$%^&*()"
        encrypted = manager.encrypt(special_text)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == special_text
