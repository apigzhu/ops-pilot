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

    # ---- AI 故障诊断（OpenAI 兼容接口）----
    # 不填 API Key 时自动降级为规则诊断
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_timeout: int = 30
    # 告警触发时是否自动调用 AI 诊断
    llm_auto_diagnose: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
