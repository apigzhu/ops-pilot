import type { Alert, Host, Metric } from "./types";

const BASE = "/api/v1";

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`请求失败 ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

export const api = {
  hosts: () => getJSON<Host[]>(`${BASE}/hosts`),
  metrics: (hostId: number) =>
    getJSON<Metric[]>(`${BASE}/metrics/${hostId}?limit=120`),
  alerts: () => getJSON<Alert[]>(`${BASE}/alerts?limit=50`),
};
