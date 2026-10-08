"""Pydantic 数据模型（请求 / 响应）。"""
from datetime import datetime

from pydantic import BaseModel, Field


class MetricIn(BaseModel):
    """Agent 上报的指标。"""

    hostname: str
    ip_address: str | None = None
    platform: str | None = None
    collected_at: datetime | None = None

    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    disk_percent: float = Field(ge=0, le=100)
    load_1m: float | None = None
    net_sent_mb: float | None = None
    net_recv_mb: float | None = None


class HostOut(BaseModel):
    """主机列表返回结构。"""

    id: int
    hostname: str
    ip_address: str | None
    platform: str | None
    last_seen: datetime

    model_config = {"from_attributes": True}


class MetricOut(BaseModel):
    """指标返回结构。"""

    collected_at: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_1m: float | None
    net_sent_mb: float | None
    net_recv_mb: float | None

    model_config = {"from_attributes": True}
