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
        case_sensitive=True,
        extra="ignore",  # 忽略未定义的环境变量
    )

    # 应用配置
    APP_NAME: str = "Stock Analyzer"
    APP_VERSION: str = "1.1.0"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me-in-production"

    # 数据库配置
    DATABASE_URL: str = (
        "postgresql+asyncpg://stockanalyzer:stockanalyzer123@"
        "localhost:5432/stock_analyzer"
    )

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # 数据源配置
    TUSHARE_TOKEN: str = ""

    # 分析配置
    ANALYSIS_DAYS: int = 120
    ANALYSIS_MIN_DAYS: int = 20

    # 加密配置
    ENCRYPTION_KEY: str = ""

    # OpenAI配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Anthropic配置
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"

    # 飞书配置
    FEISHU_WEBHOOK_URL: str = ""
    FEISHU_PUSH_ENABLED: bool = False


# 创建全局配置实例
settings = Settings()
