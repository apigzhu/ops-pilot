"""AI 辅助故障诊断。

流程：收集告警上下文（告警 + 主机 + 最近指标）→ 调用 OpenAI 兼容的
Chat Completions 接口 → 返回结构化的故障诊断。

未配置 LLM_API_KEY 时自动降级为规则诊断，保证功能始终可用。
"""
import logging
from datetime import timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Alert, AlertDiagnosis, AlertRule, Host, Metric

logger = logging.getLogger("opspilot.ai")

SYSTEM_PROMPT = (
    "你是一名资深 SRE / 运维专家。用户会给你一条服务器告警，以及触发前的监控指标。"
    "请用中文给出简洁的故障诊断，严格按以下格式输出，不要有多余的话：\n"
    "【现象】一句话描述问题。\n"
    "【可能原因】列举 2-3 条最可能的原因。\n"
    "【排查建议】给出 2-3 条具体可执行的排查命令或步骤。\n"
    "【处理建议】给出 1-2 条处理或根治建议。"
)


def _collect_context(db: Session, alert: Alert) -> str:
    """拼装给大模型的上下文文本。"""
    host = db.get(Host, alert.host_id)
    rule = db.get(AlertRule, alert.rule_id)
    since = alert.triggered_at - timedelta(minutes=5)

    metrics = list(
        db.scalars(
            select(Metric)
            .where(Metric.host_id == alert.host_id, Metric.collected_at >= since)
            .order_by(Metric.collected_at.desc())
            .limit(10)
        )
    )

    lines = [
        f"告警内容：{alert.message}",
        f"告警状态：{alert.status}",
        f"触发时间：{alert.triggered_at:%Y-%m-%d %H:%M:%S}",
        f"规则：{rule.name if rule else '-'}"
        f"（{rule.metric} {rule.operator} {rule.threshold}，{rule.severity if rule else '-'}）",
        f"主机：{host.hostname if host else alert.host_id}"
        f"（{host.ip_address if host else '-'} / {host.platform if host else '-'}）",
        "",
        "触发前 5 分钟的指标（新 → 旧）：",
    ]
    if not metrics:
        lines.append("- （无指标数据）")
    for m in metrics:
        lines.append(
            f"- {m.collected_at:%H:%M:%S} "
            f"CPU={m.cpu_percent:.1f}% MEM={m.memory_percent:.1f}% "
            f"DISK={m.disk_percent:.1f}% LOAD={m.load_1m}"
        )
    return "\n".join(lines)


_RULES: dict[str, tuple[str, list[str], list[str]]] = {
    "cpu_percent": (
        "CPU 使用率持续超过阈值，主机可能出现计算资源瓶颈。",
        ["存在 CPU 密集型进程或死循环", "负载突增 / 流量高峰", "容器或进程数过多导致资源争抢"],
        [
            "top -o %CPU  查看占用最高的进程",
            "uptime  查看 1/5/15 分钟负载",
            "ps aux --sort=-%cpu | head  定位异常进程",
        ],
    ),
    "memory_percent": (
        "内存使用率持续超过阈值，可能面临 OOM 风险。",
        ["应用存在内存泄漏", "缓存 / 连接池未释放", "进程数过多占用内存"],
        [
            "free -m  查看内存与 swap 使用",
            "ps aux --sort=-%mem | head  定位内存占用最高的进程",
            "dmesg | grep -i oom  检查是否触发 OOM Killer",
        ],
    ),
    "disk_percent": (
        "磁盘使用率持续超过阈值，可能导致写入失败或服务异常。",
        ["日志文件未清理 / 轮转失效", "临时文件或备份文件堆积", "数据量增长超出预期"],
        [
            "df -h  查看各分区使用率",
            "du -sh /* 2>/dev/null | sort -h  定位大目录",
            "find / -type f -size +500M 2>/dev/null  查找大文件",
        ],
    ),
}


def _rule_based(alert: Alert, metric: str) -> str:
    """无 API Key 时的规则诊断，保证功能可用。"""
    phenomenon, causes, steps = _RULES.get(
        metric,
        (
            "指标超过告警阈值。",
            ["资源使用异常升高", "业务流量变化", "配置或依赖异常"],
            ["查看系统基础指标（CPU/内存/磁盘）", "检查应用日志", "确认最近是否有变更"],
        ),
    )
    causes_text = "\n".join(f"{i}. {c}" for i, c in enumerate(causes, 1))
    steps_text = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
    return (
        f"【现象】{phenomenon}\n"
        f"（告警：{alert.message}）\n\n"
        f"【可能原因】\n{causes_text}\n\n"
        f"【排查建议】\n{steps_text}\n\n"
        f"【处理建议】\n"
        f"1. 确认根因后再操作，避免直接重启服务掩盖问题；\n"
        f"2. 若是容量问题，评估扩容或优化配置后补充监控与告警阈值。"
    )


def _call_llm(context: str) -> str:
    """调用 OpenAI 兼容接口。"""
    settings = get_settings()
    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    resp = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            "temperature": 0.3,
        },
        timeout=settings.llm_timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def diagnose(db: Session, alert: Alert) -> AlertDiagnosis:
    """生成（或重新生成）告警的 AI 诊断结果，并落库。"""
    settings = get_settings()
    rule = db.get(AlertRule, alert.rule_id)
    metric = rule.metric if rule else "unknown"
    context = _collect_context(db, alert)

    if settings.llm_api_key:
        try:
            content = _call_llm(context)
            model = settings.llm_model
        except Exception:  # noqa: BLE001 - LLM 失败要降级，不能影响主流程
            logger.exception("LLM 调用失败，降级为规则诊断")
            content = _rule_based(alert, metric)
            model = "rule-based(fallback)"
    else:
        content = _rule_based(alert, metric)
        model = "rule-based"

    record = db.scalar(
        select(AlertDiagnosis).where(AlertDiagnosis.alert_id == alert.id)
    )
    if record is None:
        record = AlertDiagnosis(alert_id=alert.id, content=content, model=model)
        db.add(record)
    else:
        record.content = content
        record.model = model
    db.commit()
    db.refresh(record)
    return record
