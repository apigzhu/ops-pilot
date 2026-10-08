"""数据库模型。"""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Host(Base):
    """被监控的主机。"""

    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    metrics: Mapped[list["Metric"]] = relationship(
        back_populates="host", cascade="all, delete-orphan"
    )


class Metric(Base):
    """一条指标采样记录。"""

    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    host_id: Mapped[int] = mapped_column(
        ForeignKey("hosts.id", ondelete="CASCADE"), index=True
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    cpu_percent: Mapped[float] = mapped_column(Float)
    memory_percent: Mapped[float] = mapped_column(Float)
    disk_percent: Mapped[float] = mapped_column(Float)
    load_1m: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_sent_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_recv_mb: Mapped[float | None] = mapped_column(Float, nullable=True)

    host: Mapped[Host] = relationship(back_populates="metrics")
