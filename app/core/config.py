"""
配置管理

使用pydantic-settings管理环境变量配置
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 不区分大小写
        extra="ignore",  # 忽略未定义的环境变量
    )

    # 应用配置
    app_name: str = "Stock Analyzer"
    app_version: str = "1.1.0"
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"

    # 数据库配置
    database_url: str = (
        "postgresql+asyncpg://stockanalyzer:stockanalyzer123@"
        "localhost:5432/stock_analyzer"
    )

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # 数据源配置
    tushare_token: str = ""

    # 分析配置
    analysis_days: int = 120
    analysis_min_days: int = 20

    # 加密配置
    encryption_key: str = ""

    # OpenAI配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4-turbo-preview"

    # Anthropic配置
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-opus-20240229"

    # 飞书配置
    feishu_webhook_url: str = ""
    feishu_push_enabled: bool = False


# 创建全局配置实例
settings = Settings()
