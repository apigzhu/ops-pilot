"""应用配置：统一从环境变量读取。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """OpsPilot 运行配置。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OpsPilot"
    debug: bool = False

    database_url: str = (
        "postgresql+psycopg2://opspilot:opspilot@localhost:5432/opspilot"
    )
    redis_url: str = "redis://localhost:6379/0"

    # 指标保留天数（后续清理任务使用）
    metric_retention_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
