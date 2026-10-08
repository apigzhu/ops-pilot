"""OpsPilot 后端 API 冒烟测试。"""
from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


def test_metric_ingest_and_hosts() -> None:
    payload = {
        "hostname": "ci-test-host",
        "ip_address": "127.0.0.1",
        "platform": "linux",
        "cpu_percent": 12.5,
        "memory_percent": 34.0,
        "disk_percent": 56.0,
    }
    with TestClient(app) as client:
        resp = client.post("/api/v1/metrics", json=payload)
        assert resp.status_code == 201

        hosts = client.get("/api/v1/hosts").json()
        assert any(h["hostname"] == "ci-test-host" for h in hosts)


def test_alert_rule_and_prometheus_metrics() -> None:
    rule = {
        "name": "CI CPU rule",
        "metric": "cpu_percent",
        "operator": ">",
        "threshold": 90,
        "duration_seconds": 0,
        "severity": "warning",
        "enabled": True,
    }
    with TestClient(app) as client:
        resp = client.post("/api/v1/alert-rules", json=rule)
        assert resp.status_code == 201

        rules = client.get("/api/v1/alert-rules").json()
        assert any(r["name"] == "CI CPU rule" for r in rules)

        prom = client.get("/metrics")
        assert prom.status_code == 200
        assert "opspilot_hosts_total" in prom.text
