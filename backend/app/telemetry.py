"""Prometheus 指标暴露。

/ metrics 端点输出 Prometheus 文本格式，供 Prometheus 定期抓取。
"""
from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Host, Metric

# 业务计数器
METRICS_INGESTED = Counter(
    "opspilot_metrics_ingested_total", "OpsPilot 接收的指标上报总数"
)
ALERTS_FIRED = Counter("opspilot_alerts_fired_total", "OpsPilot 触发的告警总数")

# 运行时状态（抓取时刷新）
HOSTS_TOTAL = Gauge("opspilot_hosts_total", "OpsPilot 监控的主机数量")
ALERTS_FIRING = Gauge("opspilot_alerts_firing", "OpsPilot 当前活跃告警数量")
METRICS_STORED = Gauge("opspilot_metrics_stored", "OpsPilot 已存储的指标样本总数")

router = APIRouter(tags=["telemetry"])


@router.get("/metrics")
def prometheus_metrics(db: Session = Depends(get_db)) -> Response:
    """输出 Prometheus 格式指标。"""
    HOSTS_TOTAL.set(db.scalar(select(func.count()).select_from(Host)) or 0)
    ALERTS_FIRING.set(
        db.scalar(
            select(func.count()).select_from(Alert).where(Alert.status == "firing")
        )
        or 0
    )
    METRICS_STORED.set(db.scalar(select(func.count()).select_from(Metric)) or 0)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
