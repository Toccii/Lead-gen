"use client";

import { useEffect, useState, type FormEvent } from "react";

import DashboardShell from "@/components/DashboardShell";
import { apiJson } from "@/lib/api";
import type { SystemSettings } from "@/lib/types";

const WEEKDAYS = [
  { value: 0, label: "Lunedì" },
  { value: 1, label: "Martedì" },
  { value: 2, label: "Mercoledì" },
  { value: 3, label: "Giovedì" },
  { value: 4, label: "Venerdì" },
  { value: 5, label: "Sabato" },
  { value: 6, label: "Domenica" },
];

const HOURS = Array.from({ length: 24 }, (_, h) => h);

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    apiJson<SystemSettings>("/system-settings").then(setSettings).catch(() => undefined);
  }, []);

  function update<K extends keyof SystemSettings>(key: K, value: SystemSettings[K]) {
    setSettings((s) => (s ? { ...s, [key]: value } : s));
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!settings) return;
    setSaving(true);
    setMessage(null);
    try {
      await apiJson("/system-settings", {
        method: "PUT",
        body: JSON.stringify({
          max_emails_per_day: settings.max_emails_per_day,
          weekly_job_day_of_week: settings.weekly_job_day_of_week,
          weekly_job_hour: settings.weekly_job_hour,
          daily_job_hour: settings.daily_job_hour,
          default_followup_delay_business_days: settings.default_followup_delay_business_days,
          default_close_after_days: settings.default_close_after_days,
        }),
      });
      setMessage("Salvato.");
    } catch {
      setMessage("Errore nel salvataggio.");
    } finally {
      setSaving(false);
    }
  }

  if (!settings) {
    return (
      <DashboardShell>
        <p className="text-gray-500 text-sm">Caricamento...</p>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell>
      <h1 className="text-lg font-semibold mb-2">Impostazioni</h1>
      <p className="text-sm text-gray-500 mb-4 max-w-xl">
        Il cron della piattaforma di hosting gira ogni ora; questi valori determinano
        in quale finestra oraria (fuso Europe/Rome) i job settimanale e giornaliero
        eseguono davvero il lavoro.
      </p>
      {message && <p className="text-sm mb-4">{message}</p>}
      <form onSubmit={handleSave} className="space-y-6 max-w-md">
        <fieldset className="border rounded p-4 space-y-3">
          <legend className="text-sm font-semibold px-1">Job settimanale (sourcing + primo invio)</legend>
          <label className="block text-sm space-y-1">
            <span className="text-gray-600">Giorno della settimana</span>
            <select
              value={settings.weekly_job_day_of_week}
              onChange={(e) => update("weekly_job_day_of_week", Number(e.target.value))}
              className="input"
            >
              {WEEKDAYS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm space-y-1">
            <span className="text-gray-600">Ora</span>
            <select
              value={settings.weekly_job_hour}
              onChange={(e) => update("weekly_job_hour", Number(e.target.value))}
              className="input"
            >
              {HOURS.map((h) => (
                <option key={h} value={h}>
                  {String(h).padStart(2, "0")}:00
                </option>
              ))}
            </select>
          </label>
        </fieldset>

        <fieldset className="border rounded p-4 space-y-3">
          <legend className="text-sm font-semibold px-1">Job giornaliero (risposte + follow-up)</legend>
          <label className="block text-sm space-y-1">
            <span className="text-gray-600">Ora</span>
            <select
              value={settings.daily_job_hour}
              onChange={(e) => update("daily_job_hour", Number(e.target.value))}
              className="input"
            >
              {HOURS.map((h) => (
                <option key={h} value={h}>
                  {String(h).padStart(2, "0")}:00
                </option>
              ))}
            </select>
          </label>
        </fieldset>

        <fieldset className="border rounded p-4 space-y-3">
          <legend className="text-sm font-semibold px-1">Valori di default</legend>
          <label className="block text-sm space-y-1">
            <span className="text-gray-600">Email massime al giorno</span>
            <input
              type="number"
              min={1}
              value={settings.max_emails_per_day}
              onChange={(e) => update("max_emails_per_day", Number(e.target.value))}
              className="input"
            />
          </label>
          <label className="block text-sm space-y-1">
            <span className="text-gray-600">Follow-up dopo (giorni lavorativi) — default per nuove campagne</span>
            <input
              type="number"
              min={1}
              value={settings.default_followup_delay_business_days}
              onChange={(e) => update("default_followup_delay_business_days", Number(e.target.value))}
              className="input"
            />
          </label>
          <label className="block text-sm space-y-1">
            <span className="text-gray-600">Chiusura dopo (giorni) — default per nuove campagne</span>
            <input
              type="number"
              min={1}
              value={settings.default_close_after_days}
              onChange={(e) => update("default_close_after_days", Number(e.target.value))}
              className="input"
            />
          </label>
        </fieldset>

        <button type="submit" disabled={saving} className="bg-black text-white rounded px-4 py-2 text-sm disabled:opacity-50">
          {saving ? "Salvataggio..." : "Salva"}
        </button>
      </form>
    </DashboardShell>
  );
}
