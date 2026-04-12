"""敏感数据加密模块"""

from cryptography.fernet import Fernet


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
