"""
API 路径常量

集中定义所有 API 路径，避免硬编码分散在代码各处。

使用方式:
    from app.api.paths import API_HEALTH, API_ANALYZE

    response = client.get(API_HEALTH)
"""

# API 前缀
API_PREFIX = "/api"
API_V1_PREFIX = f"{API_PREFIX}/v1"

# Health 相关
API_HEALTH = f"{API_V1_PREFIX}/health"
API_READY = f"{API_V1_PREFIX}/ready"

# 分析相关
API_ANALYZE = f"{API_V1_PREFIX}/analysis/analyze"
API_ANALYZE_BATCH = f"{API_V1_PREFIX}/analysis/analyze/batch"
API_ANALYSIS_STATUS = f"{API_V1_PREFIX}/analysis/status"

# 订阅相关
API_SUBSCRIBE = f"{API_V1_PREFIX}/subscribe"
API_SUBSCRIBE_BATCH = f"{API_V1_PREFIX}/subscribe/batch"
API_SUBSCRIPTIONS = f"{API_V1_PREFIX}/subscriptions"

# 报告相关
API_REPORT = f"{API_V1_PREFIX}/report"

# 配置相关
API_CONFIG = f"{API_V1_PREFIX}/config"
