"""告警评估引擎与通知。

后台线程每隔 alert_eval_interval 秒检查一次：
  1. 遍历所有启用的告警规则 × 所有主机
  2. 取持续时间内所有指标样本，若全部越界 → 触发告警
  3. 之前触发过、现在恢复正常 → 标记 resolved
"""
import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import Alert, AlertRule, Host, Metric

logger = logging.getLogger("opspilot.alerting")

_OPERATORS: dict[str, Callable[[float, float], bool]] = {
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
}


def _violates(value: float, rule: AlertRule) -> bool:
    """判断指标值是否违反规则。"""
    func = _OPERATORS.get(rule.operator)
    return bool(func and func(value, rule.threshold))


def notify(message: str) -> None:
    """发送告警通知：始终写日志，配置了 webhook 时额外推送。"""
    logger.warning("[ALERT] %s", message)
    url = get_settings().alert_webhook_url
    if not url:
        return
    try:
        httpx.post(
            url,
            json={"msgtype": "text", "text": {"content": message}},
            timeout=5,
        )
    except Exception:  # noqa: BLE001 - 通知失败不能影响评估
        logger.exception("告警 webhook 发送失败")


def _evaluate_host(db: Session, rule: AlertRule, host: Host, now: datetime) -> None:
    """针对单台主机评估单条规则。"""
    since = now - timedelta(seconds=rule.duration_seconds)
    samples = list(
        db.scalars(
            select(Metric)
            .where(Metric.host_id == host.id, Metric.collected_at >= since)
            .order_by(Metric.collected_at.desc())
        )
    )
    values = [getattr(s, rule.metric) for s in samples]
    values = [v for v in values if v is not None]

    triggered = bool(values) and all(_violates(v, rule) for v in values)
    current = values[0] if values else None

    firing = db.scalar(
        select(Alert).where(
            Alert.rule_id == rule.id,
            Alert.host_id == host.id,
            Alert.status == "firing",
        )
    )

    if triggered and firing is None:
        alert = Alert(
            rule_id=rule.id,
            host_id=host.id,
            value=current,
            status="firing",
            triggered_at=now,
            message=(
                f"[{rule.severity.upper()}] {host.hostname} "
                f"{rule.metric} {rule.operator} {rule.threshold} "
                f"(当前 {current:.2f})"
            ),
        )
        db.add(alert)
        db.commit()
        notify(alert.message)
    elif not triggered and firing is not None:
        firing.status = "resolved"
        firing.resolved_at = now
        db.commit()
        logger.info("告警已恢复：rule=%s host=%s", rule.name, host.hostname)


def evaluate_once() -> None:
    """执行一轮告警评估。"""
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        rules = list(db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True))))
        hosts = list(db.scalars(select(Host)))
        for rule in rules:
            for host in hosts:
                try:
                    _evaluate_host(db, rule, host, now)
                except Exception:  # noqa: BLE001
                    db.rollback()
                    logger.exception("评估失败：rule=%s host=%s", rule.name, host.hostname)


def _worker() -> None:
    interval = get_settings().alert_eval_interval
    logger.info("告警评估线程启动，检查间隔 %ss", interval)
    while True:
        try:
            evaluate_once()
        except Exception:  # noqa: BLE001
            logger.exception("告警评估循环异常")
        time.sleep(interval)


def start_worker() -> None:
    """启动后台告警评估线程（守护线程，随进程退出）。"""
    threading.Thread(target=_worker, name="opspilot-alerting", daemon=True).start()
