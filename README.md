# OpsPilot 智能运维监控平台

一个轻量级运维监控平台：自研 Agent 采集主机指标，后端接收存储，支持主机与指标查询。
目标是用「开发」的方式解决真实运维问题，覆盖监控、采集、容器化、自动化等运维开发核心能力。

## 功能特性（Phase 1）

- **主机指标采集**：Agent 基于 psutil 采集 CPU、内存、磁盘、网络、负载
- **指标上报**：Agent 定时通过 HTTP 上报到后端，支持配置地址与间隔
- **后端 API**：FastAPI 提供指标写入 / 主机列表 / 指标查询 / 健康检查
- **数据存储**：PostgreSQL 持久化主机与指标数据
- **一键部署**：Docker Compose 编排后端 + PostgreSQL + Redis + Agent

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 / FastAPI / SQLAlchemy 2.0 / Pydantic v2 |
| 数据库 | PostgreSQL 16 / Redis 7 |
| Agent | Python / psutil / httpx |
| 部署 | Docker / Docker Compose |

## 目录结构

```
ops-pilot/
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── api/        # 接口路由（metrics / hosts）
│   │   ├── config.py   # 配置
│   │   ├── database.py # 数据库会话
│   │   ├── models.py   # ORM 模型
│   │   ├── schemas.py  # Pydantic 模型
│   │   └── main.py     # 应用入口
│   ├── Dockerfile
│   └── requirements.txt
├── agent/              # 监控 Agent
│   ├── agent.py
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

## 快速开始

### 方式一：Docker Compose 一键启动（推荐）

```bash
docker compose up -d --build
```

启动后：

- 后端 API：http://localhost:8000
- 接口文档（Swagger）：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

查看日志：

```bash
docker compose logs -f agent      # 看 Agent 上报
docker compose logs -f backend    # 看后端
```

停止：

```bash
docker compose down          # 停止并保留数据
docker compose down -v       # 停止并删除数据
```

### 方式二：本地开发（不用 Docker）

```bash
# 1. 启动数据库（用 Docker 只跑 PostgreSQL + Redis）
docker compose up -d postgres redis

# 2. 安装后端依赖并启动
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. 另开终端，启动 Agent
cd agent
pip install -r requirements.txt
python agent.py
```

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| POST | `/api/v1/metrics` | Agent 上报指标 |
| GET | `/api/v1/hosts` | 主机列表 |
| GET | `/api/v1/metrics/{host_id}` | 查询某主机指标 |

示例：查询主机列表

```bash
curl http://localhost:8000/api/v1/hosts
```

## 后续规划

- [ ] Phase 2：接入 Prometheus + Grafana，告警规则与钉钉/飞书通知
- [ ] Phase 3：日志采集与检索（Loki）
- [ ] Phase 4：AI 辅助故障诊断（LLM 分析告警与日志）
- [ ] Phase 5：Kubernetes 部署 + CI/CD 流水线
