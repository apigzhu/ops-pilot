"""主机列表接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Host
from app.schemas import HostOut

router = APIRouter(prefix="/api/v1/hosts", tags=["hosts"])


@router.get("", response_model=list[HostOut])
def list_hosts(db: Session = Depends(get_db)) -> list[Host]:
    """列出所有已上报过指标的主机，最近活跃的排在前面。"""
    return list(db.scalars(select(Host).order_by(Host.last_seen.desc())))
