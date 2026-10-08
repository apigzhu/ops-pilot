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


class AlertRuleIn(BaseModel):
    """创建告警规则的请求体。"""

    name: str = Field(min_length=1, max_length=128)
    metric: str = Field(pattern="^(cpu_percent|memory_percent|disk_percent)$")
    operator: str = Field(pattern="^(>|>=|<|<=)$")
    threshold: float
    duration_seconds: int = Field(default=60, ge=0)
    severity: str = Field(default="warning", pattern="^(warning|critical)$")
    enabled: bool = True


class AlertRuleOut(AlertRuleIn):
    """告警规则返回结构。"""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    """告警事件返回结构。"""

    id: int
    rule_id: int
    host_id: int
    value: float | None
    status: str
    message: str
    triggered_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}
