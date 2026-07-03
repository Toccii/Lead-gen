"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";

import DashboardShell from "@/components/DashboardShell";
import { apiJson } from "@/lib/api";
import type { Campaign } from "@/lib/types";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setCampaigns(await apiJson<Campaign[]>("/campaigns"));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await apiJson("/campaigns", { method: "POST", body: JSON.stringify({ name: newName }) });
      setNewName("");
      await load();
    } catch {
      setError("Impossibile creare la campagna (nome gia' in uso?).");
    } finally {
      setCreating(false);
    }
  }

  return (
    <DashboardShell>
      <h1 className="text-lg font-semibold mb-4">Campagne</h1>
      <form onSubmit={handleCreate} className="flex gap-2 mb-6">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Nome nuova campagna"
          className="border rounded px-3 py-2 text-sm flex-1 max-w-sm"
        />
        <button disabled={creating} className="bg-black text-white rounded px-4 py-2 text-sm disabled:opacity-50">
          Crea
        </button>
      </form>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      <div className="border rounded divide-y max-w-2xl">
        {campaigns.map((c) => (
          <Link
            key={c.id}
            href={`/campaigns/${c.id}`}
            className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-white/5"
          >
            <div>
              <div className="font-medium">{c.name}</div>
              <div className="text-xs text-gray-500">
                {c.max_leads_per_cycle} lead/ciclo &middot; follow-up dopo {c.followup_delay_business_days}gg lavorativi
              </div>
            </div>
            <span className={`text-xs px-2 py-0.5 rounded ${c.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
              {c.is_active ? "attiva" : "disattiva"}
            </span>
          </Link>
        ))}
        {campaigns.length === 0 && (
          <div className="px-4 py-6 text-center text-gray-400 text-sm">Nessuna campagna. Creane una sopra.</div>
        )}
      </div>
    </DashboardShell>
  );
}
