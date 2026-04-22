"""
加密工具测试

测试API Key加密存储功能
"""

import pytest

from app.utils.encryption import (
    EncryptionError,
    EncryptionManager,
    generate_encryption_key,
)


class TestEncryptionManager:
    """测试加密管理器"""

    def test_init_with_valid_key(self):
        """测试使用有效密钥初始化"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)
        assert manager is not None

    def test_init_without_key(self):
        """测试缺少密钥"""
        with pytest.raises(EncryptionError):
            EncryptionManager("")

    def test_encrypt_decrypt(self):
        """测试加密解密"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        plaintext = "sk-test-api-key-123456"
        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)

        assert encrypted != plaintext
        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """测试加密空字符串"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        encrypted = manager.encrypt("")
        assert encrypted == ""

    def test_decrypt_empty_string(self):
        """测试解密空字符串"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        decrypted = manager.decrypt("")
        assert decrypted == ""

    def test_decrypt_invalid_data(self):
        """测试解密无效数据"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        with pytest.raises(EncryptionError):
            manager.decrypt("invalid-encrypted-data")

    def test_derive_key_from_password(self):
        """测试从密码派生密钥"""
        password = "my-secret-password"
        manager = EncryptionManager(password)

        plaintext = "test-data"
        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == plaintext

    def test_different_keys_different_encryption(self):
        """测试不同密钥产生不同加密结果"""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        manager1 = EncryptionManager(key1)
        manager2 = EncryptionManager(key2)

        plaintext = "test-data"
        encrypted1 = manager1.encrypt(plaintext)
        encrypted2 = manager2.encrypt(plaintext)

        assert encrypted1 != encrypted2


class TestGenerateEncryptionKey:
    """测试密钥生成"""

    def test_generate_key(self):
        """测试生成密钥"""
        key = generate_encryption_key()
        assert isinstance(key, str)
        assert len(key) == 44  # Base64编码的32字节密钥

    def test_generate_unique_keys(self):
        """测试生成唯一密钥"""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        assert key1 != key2


class TestEncryptionManagerAdvanced:
    """测试加密管理器高级功能"""

    def test_init_with_derived_key_short_password(self):
        """测试使用短密码（需要派生密钥）初始化"""
        # 短于44字符的密码会触发密钥派生
        manager = EncryptionManager("short-password")
        assert manager is not None

    def test_init_with_fernet_key_directly(self):
        """测试使用标准Fernet密钥（44字符）直接初始化"""
        key = generate_encryption_key()  # 44字符的标准Fernet密钥
        manager = EncryptionManager(key)
        assert manager is not None

    def test_encrypt_with_unicode(self):
        """测试加密Unicode字符串"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        plaintext = "API密钥测试-中文"
        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == plaintext

    def test_decrypt_with_wrong_key_fails(self):
        """测试使用错误密钥解密会失败"""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()
        manager1 = EncryptionManager(key1)
        manager2 = EncryptionManager(key2)

        plaintext = "secret-data"
        encrypted = manager1.encrypt(plaintext)

        # 使用不同密钥解密应该失败
        with pytest.raises(EncryptionError):
            manager2.decrypt(encrypted)


class TestEncryptionRandomSalt:
    """测试随机 salt 功能"""

    def test_random_salt_each_encryption(self) -> None:
        """测试每次加密使用不同的 salt"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        plaintext = "test-api-key"
        encrypted1 = manager.encrypt(plaintext)
        encrypted2 = manager.encrypt(plaintext)

        # 相同明文，不同加密结果（因为随机 salt）
        assert encrypted1 != encrypted2

    def test_decrypt_with_random_salt(self) -> None:
        """测试解密随机 salt 加密的数据"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        plaintext = "my-secret-key-12345"
        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypted_data_format(self) -> None:
        """测试加密数据格式包含版本"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        plaintext = "test-key"
        encrypted = manager.encrypt(plaintext)

        # 格式应该是 v2:base64_salt:base64_encrypted
        assert encrypted.startswith("v2:")
        parts = encrypted.split(":")
        assert len(parts) == 3


class TestEncryptionBackwardCompatibility:
    """测试向后兼容性"""

    def test_decrypt_legacy_format(self) -> None:
        """测试解密旧格式数据（固定 salt）"""
        import base64

        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        password = "test-password"
        plaintext = "legacy-api-key"

        # 使用旧方法加密（固定 salt）
        salt = b"stock_analyzer_encryption_salt_v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        legacy_encrypted = fernet.encrypt(plaintext.encode()).decode()

        # 使用新方法解密（应该能解密旧格式）
        manager = EncryptionManager(password)
        decrypted = manager.decrypt(legacy_encrypted)

        assert decrypted == plaintext

    def test_decrypt_new_format(self) -> None:
        """测试解密新格式数据"""
        key = generate_encryption_key()
        manager = EncryptionManager(key)

        plaintext = "new-format-key"
        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == plaintext

    def test_mixed_format_decryption(self) -> None:
        """测试混合格式解密"""
        import base64

        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        password = "test-password"
        manager = EncryptionManager(password)

        # 旧格式加密
        salt = b"stock_analyzer_encryption_salt_v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        legacy_encrypted = fernet.encrypt(b"legacy-key").decode()

        # 新格式加密
        new_encrypted = manager.encrypt("new-key")

        # 都能解密
        assert manager.decrypt(legacy_encrypted) == "legacy-key"
        assert manager.decrypt(new_encrypted) == "new-key"
