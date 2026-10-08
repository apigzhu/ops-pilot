import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { Alert, Diagnosis, Host, Metric } from "./types";
import MetricChart from "./components/MetricChart";

const REFRESH_MS = 5000;

function fmtTime(iso: string): string {
  return new Date(iso).toLocaleString();
}

export default function App() {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [diagnoses, setDiagnoses] = useState<Record<number, Diagnosis>>({});
  const [loadingId, setLoadingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 定期拉取主机列表 + 告警
  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const [hs, as] = await Promise.all([api.hosts(), api.alerts()]);
        if (!alive) return;
        setHosts(hs);
        setAlerts(as);
        setError(null);
        setSelectedId((cur) => (cur === null ? (hs[0]?.id ?? null) : cur));
      } catch (e) {
        if (alive) setError((e as Error).message);
      }
    };
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  // 定期拉取选中主机的指标
  useEffect(() => {
    if (selectedId === null) return;
    let alive = true;
    const load = async () => {
      try {
        const ms = await api.metrics(selectedId);
        if (alive) setMetrics(ms);
      } catch (e) {
        if (alive) setError((e as Error).message);
      }
    };
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [selectedId]);

  const latest = metrics[0];
  const selectedHost = hosts.find((h) => h.id === selectedId);
  const firing = useMemo(
    () => alerts.filter((a) => a.status === "firing"),
    [alerts]
  );

  const pct = (v: number | undefined) =>
    v === undefined ? "--" : `${v.toFixed(1)}%`;

  const runDiagnose = async (alertId: number) => {
    setLoadingId(alertId);
    try {
      const d = await api.diagnose(alertId);
      setDiagnoses((prev) => ({ ...prev, [alertId]: d }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">⚓</span> OpsPilot
          <span className="subtitle">运维监控平台</span>
        </div>
        <div className={error ? "status status-error" : "status status-ok"}>
          {error ? `⚠ ${error}` : "● 实时监控中"}
        </div>
      </header>

      <section className="cards">
        <div className="card">
          <div className="card-label">监控主机</div>
          <div className="card-value">{hosts.length}</div>
        </div>
        <div className="card">
          <div className="card-label">CPU</div>
          <div className="card-value">{pct(latest?.cpu_percent)}</div>
        </div>
        <div className="card">
          <div className="card-label">内存</div>
          <div className="card-value">{pct(latest?.memory_percent)}</div>
        </div>
        <div className="card">
          <div className="card-label">磁盘</div>
          <div className="card-value">{pct(latest?.disk_percent)}</div>
        </div>
        <div className={firing.length ? "card card-alert" : "card"}>
          <div className="card-label">活跃告警</div>
          <div className="card-value">{firing.length}</div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>指标趋势</h2>
          <select
            value={selectedId ?? ""}
            onChange={(e) => setSelectedId(Number(e.target.value))}
          >
            {hosts.map((h) => (
              <option key={h.id} value={h.id}>
                {h.hostname}
              </option>
            ))}
          </select>
        </div>
        {selectedHost && (
          <div className="host-meta">
            主机：{selectedHost.hostname} · {selectedHost.ip_address} ·{" "}
            {selectedHost.platform} · 最后上报 {fmtTime(selectedHost.last_seen)}
          </div>
        )}
        <MetricChart metrics={metrics} />
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>告警事件</h2>
          <span className="muted">
            共 {alerts.length} 条 · 活跃 {firing.length}
          </span>
        </div>
        <div className="alert-list">
          {alerts.length === 0 && <div className="muted">暂无告警</div>}
          {alerts.map((a) => {
            const d = diagnoses[a.id];
            return (
              <div key={a.id} className={`alert-row ${a.status}`}>
                <div className="alert-main">
                  <span className={`badge ${a.status}`}>
                    {a.status === "firing" ? "告警中" : "已恢复"}
                  </span>
                  <span className="alert-msg">{a.message}</span>
                  <span className="alert-time">{fmtTime(a.triggered_at)}</span>
                  <button
                    className="btn-ai"
                    onClick={() => runDiagnose(a.id)}
                    disabled={loadingId === a.id}
                  >
                    {loadingId === a.id ? "诊断中…" : "🤖 AI 诊断"}
                  </button>
                </div>
                {d && (
                  <div className="diagnosis">
                    <div className="diagnosis-head">
                      AI 诊断结果 · 模型 {d.model} · {fmtTime(d.created_at)}
                    </div>
                    <pre className="diagnosis-body">{d.content}</pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
