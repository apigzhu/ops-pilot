export interface Host {
  id: number;
  hostname: string;
  ip_address: string | null;
  platform: string | null;
  last_seen: string;
}

export interface Metric {
  collected_at: string;
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  load_1m: number | null;
  net_sent_mb: number | null;
  net_recv_mb: number | null;
}

export interface Alert {
  id: number;
  rule_id: number;
  host_id: number;
  value: number | null;
  status: "firing" | "resolved" | string;
  message: string;
  triggered_at: string;
  resolved_at: string | null;
}

export interface Diagnosis {
  alert_id: number;
  content: string;
  model: string;
  created_at: string;
}
