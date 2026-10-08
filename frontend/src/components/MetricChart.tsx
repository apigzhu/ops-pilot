import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import type { Metric } from "../types";

const SERIES = [
  { key: "cpu_percent", name: "CPU", color: "#38bdf8" },
  { key: "memory_percent", name: "内存", color: "#a78bfa" },
  { key: "disk_percent", name: "磁盘", color: "#34d399" },
] as const;

export default function MetricChart({ metrics }: { metrics: Metric[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) {
      chartRef.current = echarts.init(ref.current);
    }
    const data = [...metrics].reverse();
    chartRef.current.setOption({
      backgroundColor: "transparent",
      tooltip: { trigger: "axis" },
      legend: {
        data: SERIES.map((s) => s.name),
        textStyle: { color: "#cbd5e1" },
        top: 8,
      },
      grid: { left: 52, right: 24, top: 48, bottom: 32 },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: data.map((m) => new Date(m.collected_at).toLocaleTimeString()),
        axisLine: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#94a3b8" },
      },
      yAxis: {
        type: "value",
        max: 100,
        axisLabel: { formatter: "{value}%", color: "#94a3b8" },
        splitLine: { lineStyle: { color: "#1e293b" } },
      },
      series: SERIES.map((s) => ({
        name: s.name,
        type: "line",
        smooth: true,
        showSymbol: false,
        data: data.map((m) => m[s.key]),
        lineStyle: { width: 2, color: s.color },
        itemStyle: { color: s.color },
        areaStyle: { color: s.color, opacity: 0.08 },
      })),
    });
  }, [metrics]);

  useEffect(() => {
    const onResize = () => chartRef.current?.resize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return <div ref={ref} className="chart" />;
}
