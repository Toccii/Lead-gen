"use client";

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useParams, useRouter } from "next/navigation";

import DashboardShell from "@/components/DashboardShell";
import { apiJson } from "@/lib/api";
import type { Campaign, ExecutionLog } from "@/lib/types";

type FormState = {
  name: string;
  is_active: boolean;
  industries: string;
  geography: string;
  target_roles: string;
  keywords: string;
  company_size_min: string;
  company_size_max: string;
  max_leads_per_cycle: string;
  email_tone_of_voice: string;
  followup_offer_text: string;
  followup_delay_business_days: string;
  close_after_days: string;
};

function toForm(c: Campaign): FormState {
  return {
    name: c.name,
    is_active: c.is_active,
    industries: c.industries.join(", "),
    geography: c.geography.join(", "),
    target_roles: c.target_roles.join(", "),
    keywords: c.keywords.join(", "),
    company_size_min: c.company_size_min?.toString() ?? "",
    company_size_max: c.company_size_max?.toString() ?? "",
    max_leads_per_cycle: c.max_leads_per_cycle.toString(),
    email_tone_of_voice: c.email_tone_of_voice ?? "",
    followup_offer_text: c.followup_offer_text ?? "",
    followup_delay_business_days: c.followup_delay_business_days.toString(),
    close_after_days: c.close_after_days.toString(),
  };
}

function splitList(value: string): string[] {
  return value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean);
}

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [form, setForm] = useState<FormState | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [sourcingRunning, setSourcingRunning] = useState(false);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);

  async function load() {
    const campaign = await apiJson<Campaign>(`/campaigns/${params.id}`);
    setForm(toForm(campaign));
    const allLogs = await apiJson<ExecutionLog[]>(`/execution-logs?campaign_id=${params.id}`);
    setLogs(allLogs);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => (f ? { ...f, [key]: value } : f));
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    setMessage(null);
    try {
      await apiJson(`/campaigns/${params.id}`, {
        method: "PUT",
        body: JSON.stringify({
          name: form.name,
          is_active: form.is_active,
          industries: splitList(form.industries),
          geography: splitList(form.geography),
          target_roles: splitList(form.target_roles),
          keywords: splitList(form.keywords),
          company_size_min: form.company_size_min ? Number(form.company_size_min) : null,
          company_size_max: form.company_size_max ? Number(form.company_size_max) : null,
          max_leads_per_cycle: Number(form.max_leads_per_cycle),
          email_tone_of_voice: form.email_tone_of_voice || null,
          followup_offer_text: form.followup_offer_text || null,
          followup_delay_business_days: Number(form.followup_delay_business_days),
          close_after_days: Number(form.close_after_days),
        }),
      });
      setMessage("Salvato.");
    } catch {
      setMessage("Errore nel salvataggio.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSource() {
    setSourcingRunning(true);
    setMessage(null);
    try {
      await apiJson(`/campaigns/${params.id}/source`, { method: "POST" });
      setMessage("Sourcing avviato: vedi il log qui sotto.");
      await load();
    } catch {
      setMessage("Errore durante il sourcing.");
    } finally {
      setSourcingRunning(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Cancellare questa campagna? Possibile solo se non ha lead associati.")) return;
    try {
      await apiJson(`/campaigns/${params.id}`, { method: "DELETE" });
      router.push("/campaigns");
    } catch {
      setMessage("Impossibile cancellare: la campagna ha lead associati. Disattivala invece (Attiva = no).");
    }
  }

  if (!form) {
    return (
      <DashboardShell>
        <p className="text-gray-500 text-sm">Caricamento...</p>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell>
      <div className="flex items-center justify-between mb-4 max-w-2xl">
        <h1 className="text-lg font-semibold">{form.name}</h1>
        <div className="flex gap-2">
          <button
            onClick={handleSource}
            disabled={sourcingRunning}
            className="bg-black text-white rounded px-3 py-1.5 text-sm disabled:opacity-50"
          >
            {sourcingRunning ? "Sourcing in corso..." : "Genera lead ora"}
          </button>
          <button onClick={handleDelete} className="border rounded px-3 py-1.5 text-sm text-red-600">
            Elimina
          </button>
        </div>
      </div>
      {message && <p className="text-sm mb-4 max-w-2xl">{message}</p>}

      <form onSubmit={handleSave} className="space-y-6 max-w-2xl">
        <Section title="Scheda ICP (targeting)">
          <Field label="Nome campagna">
            <input value={form.name} onChange={(e) => update("name", e.target.value)} className="input" />
          </Field>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_active} onChange={(e) => update("is_active", e.target.checked)} />
            <span className="text-gray-600">Campagna attiva (inclusa nel job settimanale)</span>
          </label>
          <Field label="Settori/industria (separati da virgola)">
            <input value={form.industries} onChange={(e) => update("industries", e.target.value)} className="input" />
          </Field>
          <Field label="Area geografica (separata da virgola)">
            <input value={form.geography} onChange={(e) => update("geography", e.target.value)} className="input" />
          </Field>
          <Field label="Ruoli target (separati da virgola)">
            <input value={form.target_roles} onChange={(e) => update("target_roles", e.target.value)} className="input" />
          </Field>
          <Field label="Parole chiave (separate da virgola)">
            <input value={form.keywords} onChange={(e) => update("keywords", e.target.value)} className="input" />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Dipendenti min">
              <input
                type="number"
                value={form.company_size_min}
                onChange={(e) => update("company_size_min", e.target.value)}
                className="input"
              />
            </Field>
            <Field label="Dipendenti max">
              <input
                type="number"
                value={form.company_size_max}
                onChange={(e) => update("company_size_max", e.target.value)}
                className="input"
              />
            </Field>
          </div>
          <Field label="Lead massimi per ciclo settimanale">
            <input
              type="number"
              value={form.max_leads_per_cycle}
              onChange={(e) => update("max_leads_per_cycle", e.target.value)}
              className="input"
            />
          </Field>
        </Section>

        <Section title="Template email">
          <Field label="Tono di voce (istruzioni per la generazione con Claude)">
            <textarea
              value={form.email_tone_of_voice}
              onChange={(e) => update("email_tone_of_voice", e.target.value)}
              className="input h-24"
            />
          </Field>
          <Field label="Offerta di follow-up">
            <textarea
              value={form.followup_offer_text}
              onChange={(e) => update("followup_offer_text", e.target.value)}
              className="input h-24"
            />
          </Field>
        </Section>

        <Section title="Tempistiche">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Follow-up dopo (giorni lavorativi)">
              <input
                type="number"
                value={form.followup_delay_business_days}
                onChange={(e) => update("followup_delay_business_days", e.target.value)}
                className="input"
              />
            </Field>
            <Field label="Chiusura dopo (giorni dal follow-up)">
              <input
                type="number"
                value={form.close_after_days}
                onChange={(e) => update("close_after_days", e.target.value)}
                className="input"
              />
            </Field>
          </div>
        </Section>

        <button type="submit" disabled={saving} className="bg-black text-white rounded px-4 py-2 text-sm disabled:opacity-50">
          {saving ? "Salvataggio..." : "Salva"}
        </button>
      </form>

      <h2 className="text-sm font-semibold text-gray-500 mt-8 mb-2">Log esecuzioni per questa campagna</h2>
      <ul className="text-sm divide-y border rounded max-w-2xl">
        {logs.map((log) => (
          <li key={log.id} className="px-3 py-2 flex justify-between">
            <span>
              {log.job_type} &middot; {new Date(log.started_at).toLocaleString("it-IT")}
            </span>
            <span>{log.status}</span>
          </li>
        ))}
        {logs.length === 0 && <li className="px-3 py-2 text-gray-400">Nessuna esecuzione ancora</li>}
      </ul>
    </DashboardShell>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <fieldset className="border rounded p-4 space-y-3">
      <legend className="text-sm font-semibold px-1">{title}</legend>
      {children}
    </fieldset>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm space-y-1">
      <span className="text-gray-600">{label}</span>
      {children}
    </label>
  );
}
