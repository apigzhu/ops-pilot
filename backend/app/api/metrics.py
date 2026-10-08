"""指标上报与查询接口。"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Host, Metric
from app.schemas import MetricIn, MetricOut

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.post("", status_code=201)
def ingest_metric(payload: MetricIn, db: Session = Depends(get_db)) -> dict:
    """接收 Agent 上报的指标，主机不存在时自动创建。"""
    host = db.scalar(select(Host).where(Host.hostname == payload.hostname))
    now = datetime.now(timezone.utc)

    if host is None:
        host = Host(
            hostname=payload.hostname,
            ip_address=payload.ip_address,
            platform=payload.platform,
            last_seen=now,
        )
        db.add(host)
        db.flush()
    else:
        host.ip_address = payload.ip_address or host.ip_address
        host.platform = payload.platform or host.platform
        host.last_seen = now

    metric = Metric(
        host_id=host.id,
        collected_at=payload.collected_at or now,
        cpu_percent=payload.cpu_percent,
        memory_percent=payload.memory_percent,
        disk_percent=payload.disk_percent,
        load_1m=payload.load_1m,
        net_sent_mb=payload.net_sent_mb,
        net_recv_mb=payload.net_recv_mb,
    )
    db.add(metric)
    db.commit()
    return {"status": "ok", "host_id": host.id}


@router.get("/{host_id}", response_model=list[MetricOut])
def list_metrics(
    host_id: int,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Metric]:
    """查询某台主机的最近指标，按时间倒序。"""
    host = db.get(Host, host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="host not found")

    stmt = (
        select(Metric)
        .where(Metric.host_id == host_id)
        .order_by(Metric.collected_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))
