"""OpsPilot 后端入口。"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import alerting
from app.api import alerts, hosts, metrics
from app.database import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时建表，并启动后台告警评估线程。"""
    Base.metadata.create_all(bind=engine)
    alerting.start_worker()
    yield


app = FastAPI(title="OpsPilot", version="0.2.0", lifespan=lifespan)

app.include_router(metrics.router)
app.include_router(hosts.router)
app.include_router(alerts.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """健康检查接口，供监控/负载均衡探活。"""
    return {"status": "ok", "service": "OpsPilot"}
