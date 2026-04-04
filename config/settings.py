"""
配置管理模块

使用 pydantic-settings 管理配置，自动从环境变量读取
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置

    配置优先级：环境变量 > .env 文件 > 默认值
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "stock-analyzer"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_secret_key: str = Field(default="change-me-in-production")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/stock_analyzer"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_password: str | None = None
    redis_max_connections: int = 50

    # Tushare
    tushare_token: str = Field(default="")
    tushare_timeout: int = 10
    tushare_max_retries: int = 3

    # AKShare
    akshare_timeout: int = 15
    akshare_max_retries: int = 3

    # Cache TTL (seconds)
    cache_ttl_daily: int = 1800  # 30 minutes
    cache_ttl_realtime: int = 300  # 5 minutes
    cache_ttl_financial: int = 86400  # 24 hours

    # Circuit Breaker
    circuit_breaker_threshold: int = 3
    circuit_breaker_timeout: int = 300  # 5 minutes

    # Rate Limiting
    rate_limit_free: str = "10/minute"
    rate_limit_pro: str = "60/minute"
    rate_limit_enterprise: str = "300/minute"

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # AI (Optional)
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-opus-20240229"

    # Monitoring
    prometheus_port: int = 9090
    grafana_port: int = 3000

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    @field_validator("app_secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """验证密钥不能为默认值（生产环境）"""
        if v == "change-me-in-production" and cls.model_config.get("env") == "production":
            raise ValueError("app_secret_key must be changed in production")
        return v

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    获取配置实例（单例模式）

    使用 lru_cache 确保配置只加载一次
    """
    return Settings()


# 便捷访问
settings = get_settings()
