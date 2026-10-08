"""OpsPilot 后端入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import hosts, metrics
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时自动建表（生产环境应改用 Alembic 迁移）。"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="OpsPilot", version="0.1.0", lifespan=lifespan)

app.include_router(metrics.router)
app.include_router(hosts.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """健康检查接口，供监控/负载均衡探活。"""
    return {"status": "ok", "service": "OpsPilot"}
