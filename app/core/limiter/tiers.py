"""用户等级定义模块"""

from enum import Enum


class UserTier(str, Enum):
    """用户等级"""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    SERVICE = "service"  # 服务账号


# 限流配置（按文档7.1.1节）
RATE_LIMITS: dict[UserTier, dict[str, tuple[int, int]]] = {
    UserTier.FREE: {
        "analyze": (10, 60),  # 10次/分钟
        "batch_analyze": (2, 60),  # 2次/分钟
        "ai_enhanced": (5, 86400),  # 5次/天
    },
    UserTier.PRO: {
        "analyze": (60, 60),  # 60次/分钟
        "batch_analyze": (10, 60),  # 10次/分钟
        "ai_enhanced": (100, 2592000),  # 100次/月
    },
    UserTier.ENTERPRISE: {
        "analyze": (300, 60),  # 300次/分钟
        "batch_analyze": (30, 60),  # 30次/分钟
        "ai_enhanced": (999999, 1),  # 无限制
    },
    UserTier.SERVICE: {
        "analyze": (1000, 60),  # 1000次/分钟
        "batch_analyze": (100, 60),  # 100次/分钟
        "ai_enhanced": (999999, 1),  # 无限制
    },
}
