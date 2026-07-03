# Lead-gen — B2B Lead Generation & Outreach Automation

Sistema automatico end-to-end per lead generation B2B: sourcing (Apollo.io),
generazione email personalizzate (Claude), invio/lettura via Microsoft Graph,
follow-up automatico su giorni lavorativi italiani, dashboard web (Next.js).

Il progetto viene costruito per fasi (vedi sezione "Stato del progetto"
sotto). Questo è lo stato al termine della **Fase 5 — Dashboard**.

## Struttura del repo

```
Lead-gen/
├── backend/            FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── core/       config (env vars), security (JWT/password hashing, unsubscribe token)
│   │   ├── db/         base declarativa, sessione DB, seed utente admin
│   │   ├── models/     tabelle: campaigns, leads, email_messages, replies,
│   │   │               execution_logs, users, suppressions, system_settings
│   │   ├── schemas/    Pydantic schemas API
│   │   ├── api/        router FastAPI (auth, campaigns, leads, emails, sourcing,
│   │   │               jobs, execution-logs, metrics, unsubscribe) + auth dependency
│   │   ├── sourcing/   interfaccia pluggable + adapter Apollo/mock
│   │   ├── email/      generazione (Claude) + invio/lettura (MS Graph)
│   │   ├── followup/   logica giorni lavorativi italiani + rilevamento risposte
│   │   └── jobs/       job settimanale (Fase 6) e giornaliero (reply-check + follow-up)
│   └── alembic/        migrazioni DB
├── frontend/           Next.js (App Router, TS, Tailwind) — dashboard
│   ├── app/             login, dashboard home, lead, campagne (+ editor ICP), log
│   ├── components/       DashboardShell (nav + auth guard)
│   └── lib/              client API con JWT Bearer, auth context
├── docker-compose.yml  ambiente di sviluppo locale (Postgres + backend + frontend)
└── .env.example        tutte le variabili d'ambiente necessarie
```

## Stato del progetto (fasi)

- [x] Fase 1 — Setup progetto: struttura cartelle, schema DB, `.env.example`
- [x] Fase 2 — Scheda ICP + sourcing Apollo (con dati mock)
- [x] Fase 3 — Generazione ed invio email (dry-run di default)
- [x] Fase 4 — Rilevamento risposte + follow-up giorni lavorativi
- [x] **Fase 5 — Dashboard**: login, tabella lead con filtri, metriche/funnel,
      editor scheda ICP e template email, log esecuzioni
- [ ] Fase 6 — Scheduler/automazione finale
- [ ] Fase 7 — Deploy

## Quickstart (sviluppo locale)

1. Copia `.env.example` in `.env` nella root e compila almeno `SECRET_KEY`,
   `DASHBOARD_ADMIN_EMAIL`, `DASHBOARD_ADMIN_PASSWORD`. Le altre chiavi
   (Apollo, Anthropic, Microsoft Graph) sono opzionali finché non servono
   nelle fasi 2-4 — lascia `SOURCING_ADAPTER=mock` e `EMAIL_DRY_RUN=true`
   per lavorare senza credenziali reali.
2. Avvia lo stack:
   ```bash
   docker compose up --build
   ```
   - Backend: http://localhost:8000/health
   - Frontend: http://localhost:3000
   - Postgres: localhost:5432
3. Applica le migrazioni del database (dentro il container backend):
   ```bash
   docker compose exec backend alembic upgrade head
   ```
4. Accedi alla dashboard su http://localhost:3000/login con le credenziali
   `DASHBOARD_ADMIN_EMAIL` / `DASHBOARD_ADMIN_PASSWORD` impostate in `.env`
   (l'utente viene creato/aggiornato automaticamente all'avvio del backend).

### Sviluppo senza Docker

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://leadgen:leadgen@localhost:5432/leadgen
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## Come ottenere le credenziali

### Apollo.io
Dashboard Apollo → **Settings → Integrations → API** → genera una API key.
Impostala in `APOLLO_API_KEY` e cambia `SOURCING_ADAPTER=apollo` (disponibile
dalla Fase 2).

### Anthropic (Claude)
[console.anthropic.com](https://console.anthropic.com/settings/keys) → crea
una API key → `ANTHROPIC_API_KEY`.

### Microsoft Graph (Outlook / Microsoft 365) — registrazione app su Azure AD

Questo è il passaggio più macchinoso. Il sistema invia email dalla stessa
casella ogni settimana/giorno **senza un utente collegato** (i job girano
via cron), quindi serve un'app **app-only** (client-credentials flow), non
un login utente interattivo.

1. **Registra l'app**
   - Vai su [portal.azure.com](https://portal.azure.com) → **Microsoft Entra ID**
     (ex Azure AD) → **App registrations** → **New registration**.
   - Nome a piacere (es. "Lead-gen Outreach"), account type "Single tenant".
   - Non serve un Redirect URI (non useremo login interattivo).
   - Dopo la creazione annota **Application (client) ID** e **Directory
     (tenant) ID** → vanno in `MS_GRAPH_CLIENT_ID` e `MS_GRAPH_TENANT_ID`.

2. **Crea un client secret**
   - Nella app registrata → **Certificates & secrets** → **New client
     secret** → scegli una scadenza (es. 12/24 mesi, dovrai rinnovarlo) →
     copia subito il **Value** (non sarà più visibile dopo) →
     `MS_GRAPH_CLIENT_SECRET`.

3. **Assegna i permessi API (Application permissions, non Delegated)**
   - **API permissions** → **Add a permission** → **Microsoft Graph** →
     **Application permissions** → aggiungi:
     - `Mail.Send` (per inviare le email)
     - `Mail.ReadWrite` (per leggere le risposte nella stessa casella)
   - Clicca **Grant admin consent for <tenant>** (serve un ruolo di
     amministratore Microsoft 365/Entra ID — se non sei tu, chiedi
     all'amministratore del tenant).

4. **Limita l'accesso alla sola casella mittente (fortemente raccomandato)**
   Senza questo passaggio, l'app con permessi `Mail.Send`/`Mail.ReadWrite`
   può leggere/inviare per **qualsiasi casella del tenant**. Per limitarla a
   una sola casella (es. `outreach@tuodominio.it`), usa PowerShell con il
   modulo Exchange Online:
   ```powershell
   Connect-ExchangeOnline
   New-ApplicationAccessPolicy `
     -AppId "<MS_GRAPH_CLIENT_ID>" `
     -PolicyScopeGroupId "outreach@tuodominio.it" `
     -AccessRight RestrictAccess `
     -Description "Lead-gen: limita l'app alla sola casella outreach"
   ```
   Serve un ruolo di amministratore Exchange Online.

5. **Imposta la casella mittente**
   `MS_GRAPH_SENDER_MAILBOX=outreach@tuodominio.it` — deve essere una
   casella Microsoft 365 valida a cui hai accesso admin.

6. Lascia `MS_GRAPH_AUTH_MODE=application`.

Questi flussi di invio/lettura verranno implementati nella Fase 3 e 4; per
ora bastano le credenziali salvate in `.env`.

## Compliance (GDPR)

- Ogni lead ha un campo `legal_basis` valorizzato di default con la base
  giuridica standard (legittimo interesse B2B, art. 6.1.f GDPR).
- La tabella `suppressions` è una lista globale e permanente di opt-out,
  indipendente dai singoli lead/campagne: un indirizzo che si disiscrive non
  può essere ricontattato in nessuna campagna futura, anche se il lead
  originale viene cancellato.
- Cancellazione di un lead = diritto all'oblio, gestita a livello applicativo
  nella Fase 5/7.
