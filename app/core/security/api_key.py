"""API Key 认证模块"""

import secrets


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
        # 基本格式检查：前缀_随机字符串
        if not api_key or "_" not in api_key:
            return False

        parts = api_key.split("_", 1)
        if len(parts) != 2:
            return False

        prefix, random_part = parts

        # 前缀不能为空
        if not prefix:
            return False

        # 随机部分长度检查（至少32字符）
        if len(random_part) < 32:
            return False

        return True
