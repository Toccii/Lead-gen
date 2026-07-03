"use client";

import { useEffect, useState } from "react";

import DashboardShell from "@/components/DashboardShell";
import { apiJson } from "@/lib/api";
import type { DashboardMetrics, ExecutionLog } from "@/lib/types";

const FUNNEL_ORDER: { key: string; label: string }[] = [
  { key: "nuovo", label: "Nuovo" },
  { key: "inviata", label: "Inviata" },
  { key: "risposto", label: "Risposto" },
  { key: "follow_up_inviato", label: "Follow-up inviato" },
  { key: "chiuso_senza_risposta", label: "Chiuso senza risposta" },
  { key: "opt_out", label: "Opt-out" },
];

export default function DashboardHomePage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiJson<DashboardMetrics>("/metrics").then(setMetrics).catch((e) => setError(String(e)));
    apiJson<ExecutionLog[]>("/execution-logs")
      .then((l) => setLogs(l.slice(0, 5)))
      .catch(() => undefined);
  }, []);

  return (
    <DashboardShell>
      <h1 className="text-lg font-semibold mb-4">Dashboard</h1>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      {metrics && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <StatCard label="Lead totali" value={metrics.total_leads} />
            <StatCard label="Email inviate questa settimana" value={metrics.emails_sent_this_week} />
            <StatCard label="Tasso di risposta" value={`${(metrics.response_rate * 100).toFixed(1)}%`} />
          </div>
          <h2 className="text-sm font-semibold text-gray-500 mb-2">Funnel</h2>
          <div className="space-y-2 mb-8 max-w-xl">
            {FUNNEL_ORDER.map(({ key, label }) => (
              <FunnelBar key={key} label={label} value={metrics.funnel[key] ?? 0} max={metrics.total_leads || 1} />
            ))}
          </div>
        </>
      )}
      <h2 className="text-sm font-semibold text-gray-500 mb-2">Ultime esecuzioni</h2>
      <ul className="text-sm divide-y border rounded max-w-xl">
        {logs.map((log) => (
          <li key={log.id} className="px-3 py-2 flex justify-between">
            <span>{log.job_type}</span>
            <span
              className={
                log.status === "success"
                  ? "text-green-600"
                  : log.status === "failed"
                    ? "text-red-600"
                    : "text-gray-500"
              }
            >
              {log.status}
            </span>
          </li>
        ))}
        {logs.length === 0 && <li className="px-3 py-2 text-gray-400">Nessuna esecuzione registrata</li>}
      </ul>
    </DashboardShell>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="border rounded-lg p-4">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}

function FunnelBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = Math.round((value / max) * 100);
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded">
        <div className="h-2 bg-black rounded" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
