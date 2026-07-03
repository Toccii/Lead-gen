"use client";

import { useEffect, useState } from "react";

import DashboardShell from "@/components/DashboardShell";
import { apiJson } from "@/lib/api";
import type { ExecutionLog } from "@/lib/types";

export default function LogsPage() {
  const [logs, setLogs] = useState<ExecutionLog[]>([]);

  useEffect(() => {
    apiJson<ExecutionLog[]>("/execution-logs").then(setLogs).catch(() => undefined);
  }, []);

  return (
    <DashboardShell>
      <h1 className="text-lg font-semibold mb-4">Log delle esecuzioni</h1>
      <div className="overflow-x-auto border rounded">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-white/5 text-left">
            <tr>
              <th className="px-3 py-2">Job</th>
              <th className="px-3 py-2">Campagna</th>
              <th className="px-3 py-2">Stato</th>
              <th className="px-3 py-2">Iniziato</th>
              <th className="px-3 py-2">Terminato</th>
              <th className="px-3 py-2">Dettagli</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="border-t align-top">
                <td className="px-3 py-2 whitespace-nowrap">{log.job_type}</td>
                <td className="px-3 py-2">{log.campaign_id ?? "-"}</td>
                <td className="px-3 py-2">{log.status}</td>
                <td className="px-3 py-2 whitespace-nowrap">{new Date(log.started_at).toLocaleString("it-IT")}</td>
                <td className="px-3 py-2 whitespace-nowrap">
                  {log.finished_at ? new Date(log.finished_at).toLocaleString("it-IT") : "-"}
                </td>
                <td className="px-3 py-2">
                  <pre className="whitespace-pre-wrap text-xs">{JSON.stringify(log.summary, null, 2)}</pre>
                </td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-gray-400">
                  Nessuna esecuzione registrata
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </DashboardShell>
  );
}
