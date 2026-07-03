"use client";

import { useEffect, useState } from "react";

import DashboardShell from "@/components/DashboardShell";
import { apiJson } from "@/lib/api";
import type { Campaign, Lead, LeadStatus } from "@/lib/types";

const STATUS_OPTIONS: LeadStatus[] = [
  "nuovo",
  "inviata",
  "risposto",
  "follow_up_inviato",
  "chiuso_senza_risposta",
  "opt_out",
];

const STATUS_COLORS: Record<string, string> = {
  nuovo: "bg-gray-100 text-gray-700",
  inviata: "bg-blue-100 text-blue-700",
  risposto: "bg-green-100 text-green-700",
  follow_up_inviato: "bg-yellow-100 text-yellow-700",
  chiuso_senza_risposta: "bg-red-100 text-red-700",
  opt_out: "bg-black text-white",
};

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [campaignId, setCampaignId] = useState("");
  const [status, setStatus] = useState("");
  const [industry, setIndustry] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiJson<Campaign[]>("/campaigns").then(setCampaigns).catch(() => undefined);
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (campaignId) params.set("campaign_id", campaignId);
    if (status) params.set("status", status);
    if (industry) params.set("industry", industry);

    apiJson<Lead[]>(`/leads?${params.toString()}`)
      .then(setLeads)
      .finally(() => setLoading(false));
  }, [campaignId, status, industry]);

  return (
    <DashboardShell>
      <h1 className="text-lg font-semibold mb-4">Lead</h1>
      <div className="flex flex-wrap gap-3 mb-4">
        <select value={campaignId} onChange={(e) => setCampaignId(e.target.value)} className="border rounded px-2 py-1.5 text-sm">
          <option value="">Tutte le campagne</option>
          {campaigns.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="border rounded px-2 py-1.5 text-sm">
          <option value="">Tutti gli stati</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <input
          placeholder="Filtra per settore"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="border rounded px-2 py-1.5 text-sm"
        />
      </div>
      <div className="overflow-x-auto border rounded">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-white/5 text-left">
            <tr>
              <th className="px-3 py-2">Azienda</th>
              <th className="px-3 py-2">Contatto</th>
              <th className="px-3 py-2">Ruolo</th>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Settore</th>
              <th className="px-3 py-2">Stato</th>
              <th className="px-3 py-2">Creato</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id} className="border-t">
                <td className="px-3 py-2">{lead.company_name}</td>
                <td className="px-3 py-2">
                  {[lead.contact_first_name, lead.contact_last_name].filter(Boolean).join(" ") || "-"}
                </td>
                <td className="px-3 py-2">{lead.role_title || "-"}</td>
                <td className="px-3 py-2">{lead.email || "-"}</td>
                <td className="px-3 py-2">{lead.industry || "-"}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[lead.status] ?? ""}`}>
                    {lead.status}
                  </span>
                </td>
                <td className="px-3 py-2">{new Date(lead.created_at).toLocaleDateString("it-IT")}</td>
              </tr>
            ))}
            {!loading && leads.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-gray-400">
                  Nessun lead trovato
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </DashboardShell>
  );
}
