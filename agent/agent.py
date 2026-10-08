"""OpsPilot 监控 Agent：采集本机指标并上报到后端。

可独立运行（python agent.py），也可用 Docker 运行。
通过环境变量 BACKEND_URL / INTERVAL 配置上报地址与采集间隔。
"""
import os
import platform
import socket
import time
from datetime import datetime, timezone

import httpx
import psutil

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1/metrics")
INTERVAL = int(os.getenv("INTERVAL", "10"))


def local_ip() -> str:
    """获取本机内网 IP（不产生实际流量）。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def collect() -> dict:
    """采集一条本机指标。"""
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    try:
        load_1m = psutil.getloadavg()[0]
    except (AttributeError, OSError):
        load_1m = None
    return {
        "hostname": socket.gethostname(),
        "ip_address": local_ip(),
        "platform": f"{platform.system()} {platform.release()}",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": disk.percent,
        "load_1m": load_1m,
        "net_sent_mb": round(net.bytes_sent / 1024 / 1024, 2),
        "net_recv_mb": round(net.bytes_recv / 1024 / 1024, 2),
    }


def main() -> None:
    print(f"[OpsPilot Agent] 上报地址：{BACKEND_URL}，间隔：{INTERVAL}s")
    with httpx.Client(timeout=5) as client:
        while True:
            try:
                payload = collect()
                resp = client.post(BACKEND_URL, json=payload)
                resp.raise_for_status()
                stamp = datetime.now().strftime("%H:%M:%S")
                print(
                    f"[{stamp}] 上报成功  CPU={payload['cpu_percent']}%  "
                    f"MEM={payload['memory_percent']}%  DISK={payload['disk_percent']}%"
                )
            except Exception as exc:  # noqa: BLE001 - Agent 需要持续运行
                print(f"[!] 上报失败：{exc}")
            time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
