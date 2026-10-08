# OpsPilot 智能运维监控平台

一个轻量级运维监控平台：自研 Agent 采集主机指标，后端接收存储，支持**监控告警**、
**Web 可视化仪表盘**，并接入业界标准的 **Prometheus + Grafana** 监控体系。

目标是覆盖监控、采集、告警、可视化、容器化等运维开发核心能力。

## 功能特性

- **主机指标采集**：Agent 基于 psutil 采集 CPU、内存、磁盘、网络、负载
- **指标上报**：Agent 定时通过 HTTP 上报到后端，支持配置地址与间隔
- **后端 API**：FastAPI 提供指标写入 / 主机列表 / 指标查询 / 健康检查
- **告警引擎**：后台线程按规则评估指标，支持阈值 + 持续时间，触发/恢复全生命周期
- **告警通知**：支持 webhook（钉钉/飞书机器人）推送，未配置时写日志
- **Web 仪表盘**：React + ECharts 实时曲线、主机切换、告警列表
- **Prometheus 指标暴露**：后端 `/metrics` 输出 Prometheus 文本格式
- **Grafana 大盘**：预置数据源与仪表盘，可视化主机与业务指标
- **一键部署**：Docker Compose 编排全部 7 个服务

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 / FastAPI / SQLAlchemy 2.0 / Pydantic v2 |
| 前端 | React 18 / TypeScript / Vite / ECharts |
| 监控 | Prometheus / node-exporter / Grafana |
| 数据库 | PostgreSQL 16 / Redis 7 |
| Agent | Python / psutil / httpx |
| 部署 | Docker / Docker Compose |

## 架构

```
                    ┌──────────────┐
   Agent ──HTTP──▶  │   backend    │ ──▶ PostgreSQL
 (psutil采集)        │  (FastAPI)   │ ──▶ Redis
                    │  告警引擎     │
                    └──────┬───────┘
                           │ /metrics (Prometheus 格式)
                           ▼
   node-exporter ────▶ ┌──────────┐ ────▶ ┌─────────┐
     (主机指标)         │Prometheus│       │ Grafana │
                       └──────────┘       └─────────┘
                                              ▲
   frontend (React) ──HTTP──────────────────┘
```

## 目录结构

```
ops-pilot/
├── backend/                # FastAPI 后端
│   └── app/
│       ├── api/            # metrics / hosts / alerts
│       ├── alerting.py     # 告警评估引擎
│       ├── telemetry.py    # Prometheus 指标暴露
│       ├── models.py       # ORM 模型
│       └── main.py
├── frontend/               # React 仪表盘
├── agent/                  # 监控 Agent
├── monitoring/
│   ├── prometheus/prometheus.yml
│   └── grafana/
│       ├── provisioning/   # 数据源 + 仪表盘自动配置
│       └── dashboards/opspilot.json
└── docker-compose.yml
```

## 快速开始

### 1. 启动全部服务

```bash
docker compose up -d --build
```

| 服务 | 地址 | 说明 |
|---|---|---|
| 后端 API | http://localhost:8000 | Swagger 文档在 /docs |
| 前端仪表盘 | http://localhost:5173 | 需单独 `npm run dev` |
| Prometheus | http://localhost:9090 | 指标查询 / targets |
| Grafana | http://localhost:3000 | 账号密码 admin / admin |
| node-exporter | http://localhost:9100/metrics | 主机指标 |

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 3. 打开 Grafana 看大盘

访问 http://localhost:3000，用 `admin / admin` 登录，
左侧 **Dashboards** 里打开 **OpsPilot 运维监控**（已预置数据源，无需手动配置）。

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/metrics` | Prometheus 指标 |
| POST | `/api/v1/metrics` | Agent 上报指标 |
| GET | `/api/v1/hosts` | 主机列表 |
| GET | `/api/v1/metrics/{host_id}` | 查询某主机指标 |
| POST | `/api/v1/alert-rules` | 创建告警规则 |
| GET | `/api/v1/alert-rules` | 告警规则列表 |
| DELETE | `/api/v1/alert-rules/{id}` | 删除告警规则 |
| GET | `/api/v1/alerts` | 告警事件列表 |

## 告警功能用法

### 创建一条告警规则（CPU > 80% 持续 30 秒）

```bash
curl -X POST http://localhost:8000/api/v1/alert-rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High CPU",
    "metric": "cpu_percent",
    "operator": ">",
    "threshold": 80,
    "duration_seconds": 30,
    "severity": "critical",
    "enabled": true
  }'
```

### 查看告警事件

```bash
curl http://localhost:8000/api/v1/alerts
curl "http://localhost:8000/api/v1/alerts?status=firing"
```

### 配置通知 webhook（可选）

在 `docker-compose.yml` 的 backend 服务里设置 `ALERT_WEBHOOK_URL` 为钉钉/飞书机器人地址，
告警触发时会自动推送消息；不配置则只写后端日志。

## 自定义 Prometheus 指标

后端在 `/metrics` 暴露以下业务指标：

| 指标 | 类型 | 说明 |
|---|---|---|
| `opspilot_hosts_total` | Gauge | 监控主机数量 |
| `opspilot_alerts_firing` | Gauge | 当前活跃告警数 |
| `opspilot_metrics_stored` | Gauge | 已存储指标样本数 |
| `opspilot_metrics_ingested_total` | Counter | 累计接收指标数 |
| `opspilot_alerts_fired_total` | Counter | 累计触发告警数 |



## AI 辅助故障诊断

告警触发时，可把「告警 + 主机 + 触发前指标」整理成上下文，交给大模型生成故障诊断：

- **OpenAI 兼容接口**：支持 DeepSeek / 通义千问 / OpenAI 等
- **无 Key 自动降级**：未配置 `LLM_API_KEY` 时使用内置规则诊断，功能始终可用
- **结果落库**：诊断内容存入 `alert_diagnoses` 表，前端可查看

### 配置

在 `docker-compose.yml` 的 backend 服务里设置：

```yaml
LLM_API_KEY: "sk-xxxxxxxx"              # 你的 API Key
LLM_BASE_URL: "https://api.deepseek.com/v1"
LLM_MODEL: "deepseek-chat"
LLM_AUTO_DIAGNOSE: "false"              # 告警触发时是否自动诊断
```

### 使用

```bash
# 对某条告警执行 AI 诊断
curl -X POST http://localhost:8000/api/v1/alerts/1/diagnose

# 获取已有诊断结果
curl http://localhost:8000/api/v1/alerts/1/diagnosis
```

前端「告警事件」里每条告警都有 **🤖 AI 诊断** 按钮，点击即可生成并展开查看。

### 诊断输出示例

```
【现象】CPU 使用率持续超过阈值，主机可能出现计算资源瓶颈。
【可能原因】
1. 存在 CPU 密集型进程或死循环
2. 负载突增 / 流量高峰
3. 容器或进程数过多导致资源争抢
【排查建议】
1. top -o %CPU  查看占用最高的进程
2. uptime  查看 1/5/15 分钟负载
...
```

## Kubernetes 部署

前置：Docker Desktop → Settings → Kubernetes → 勾选 **Enable Kubernetes**。

### 1. 构建镜像（K8s 与 Docker 共用镜像仓库）

```bash
docker build -t opspilot-backend:latest  ./backend
docker build -t opspilot-agent:latest    ./agent
docker build -t opspilot-frontend:latest ./frontend
```

### 2. 部署到 K8s

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/agent.yaml
kubectl apply -f k8s/frontend.yaml
```

或者一次性：

```bash
kubectl apply -f k8s/
```

### 3. 查看状态

```bash
kubectl get pods -n opspilot -w
kubectl get svc -n opspilot
kubectl logs -n opspilot deploy/backend
```

### 4. 访问

| 服务 | 地址 | 说明 |
|---|---|---|
| 前端 | http://localhost:30080 | NodePort |
| 后端 API | `kubectl port-forward -n opspilot svc/backend 8000:8000` | 本地转发 |

### 5. 清理

```bash
kubectl delete namespace opspilot
```

### K8s 资源清单

| 文件 | 内容 |
|---|---|
| `namespace.yaml` | 命名空间 opspilot |
| `postgres.yaml` | PVC + Deployment + Service |
| `redis.yaml` | Deployment + Service |
| `backend.yaml` | Deployment（2 副本）+ Service + 健康探针 |
| `agent.yaml` | Deployment |
| `frontend.yaml` | Deployment + NodePort Service |

## 后续规划

- [x] Phase 1：指标采集 + 后端存储 + API
- [x] Phase 2：告警规则 + 告警引擎 + 通知
- [x] Phase 3：Web 可视化仪表盘（React + ECharts）
- [x] Phase 4：Prometheus + node-exporter + Grafana
- [ ] Phase 5：日志采集与检索（Loki）
- [x] Phase 6：AI 辅助故障诊断（LLM 分析告警 + 规则降级）
- [x] Phase 5：CI/CD（GitHub Actions）
- [x] Phase 6：Kubernetes 部署清单 + 本地集群部署
