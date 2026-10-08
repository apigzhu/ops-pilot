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

    # 告警评估线程的检查间隔（秒）
    alert_eval_interval: int = 10
    # 告警通知 webhook（钉钉/飞书/自定义），留空则只写日志
    alert_webhook_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
