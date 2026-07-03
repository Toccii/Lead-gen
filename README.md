# Lead-gen — B2B Lead Generation & Outreach Automation

Sistema automatico end-to-end per lead generation B2B: sourcing (Apollo.io),
generazione email personalizzate (Claude), invio/lettura via Microsoft Graph,
follow-up automatico su giorni lavorativi italiani, dashboard web (Next.js).

Il progetto viene costruito per fasi (vedi sezione "Stato del progetto"
sotto). Questo è lo stato al termine della **Fase 7 — Deploy**: tutto il
codice e la configurazione sono pronti; il deploy effettivo su Railway
richiede il tuo account (vedi sezione "Deploy su Railway" sotto).

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
│   │   └── jobs/       job settimanale e giornaliero + gate di schedulazione
│   └── alembic/        migrazioni DB
├── frontend/           Next.js (App Router, TS, Tailwind) — dashboard
│   ├── app/             login, dashboard home, lead, campagne (+ editor ICP), log
│   ├── components/       DashboardShell (nav + auth guard)
│   └── lib/              client API con JWT Bearer, auth context
├── .github/workflows/  CI (test backend + build frontend ad ogni push/PR)
├── docker-compose.yml  ambiente di sviluppo locale (Postgres + backend + frontend)
└── .env.example        tutte le variabili d'ambiente necessarie
```

`backend/railway.json` e `frontend/railway.json` contengono la
configurazione Docker di base per il deploy su Railway (Fase 7).

## Stato del progetto (fasi)

- [x] Fase 1 — Setup progetto: struttura cartelle, schema DB, `.env.example`
- [x] Fase 2 — Scheda ICP + sourcing Apollo (con dati mock)
- [x] Fase 3 — Generazione ed invio email (dry-run di default)
- [x] Fase 4 — Rilevamento risposte + follow-up giorni lavorativi
- [x] Fase 5 — Dashboard: login, tabella lead con filtri, metriche/funnel,
      editor scheda ICP e template email, log esecuzioni
- [x] Fase 6 — Scheduler/automazione finale: job settimanale (sourcing +
      primo invio) e job giornaliero (risposte + follow-up), entrambi
      collegabili al cron della piattaforma, orario configurabile da dashboard
- [x] **Fase 7 — Deploy**: `railway.json` per backend/frontend, CI GitHub
      Actions (test + build ad ogni push), guida passo-passo per Railway
      (e alternativa Render) — il deploy sul tuo account resta da fare

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

## Automazione (job settimanale + giornaliero)

Ci sono due entrypoint pensati per essere lanciati dal cron della piattaforma
di hosting:

```bash
python -m app.jobs.weekly_job   # sourcing + primo invio per le campagne attive
python -m app.jobs.daily_job    # controllo risposte + follow-up/chiusura
```

Scrivono un `ExecutionLog` per ogni esecuzione, visibile in dashboard (Log e,
per il job settimanale, anche nella pagina di dettaglio di ogni campagna).

### Perché il cron gira ogni ora, non a un orario fisso

Giorno/ora del job settimanale e ora del job giornaliero sono modificabili
dalla dashboard (pagina **Impostazioni**, tabella `system_settings`). Per
evitare di dover aggiornare la configurazione cron della piattaforma ogni
volta che cambi quell'orario, il cron è pensato per invocare gli entrypoint
**ogni ora**: la funzione stessa controlla se "adesso" (in Europe/Rome)
corrisponde al giorno/ora configurato e, se non è il momento giusto, esce
subito senza fare nulla (nessun `ExecutionLog` scritto per i "no-op"). I
pulsanti "Genera lead ora" ed "Esegui job settimanale ora" nella dashboard,
e gli endpoint `POST /jobs/*`, ignorano sempre questo controllo ed eseguono
subito.

## Deploy su Railway (Fase 7)

Railway è la piattaforma scelta (vedi confronto in Fase 1: cron nativo
semplice, `DATABASE_URL` condiviso automaticamente tra i servizi dello
stesso progetto, nessun cold-start sul piano a pagamento). Il deploy vero e
proprio richiede il tuo account Railway: creazione progetto, collegamento
del repo GitHub e inserimento delle chiavi reali sono passaggi che devi
fare tu. `backend/railway.json` e `frontend/railway.json` sono già pronti
nel repo con la configurazione Docker di base.

Il progetto Railway finale avrà **5 servizi**: Postgres + backend (web) +
frontend (web) + 2 job (cron, senza dominio pubblico).

1. **Crea il progetto**
   - [railway.app](https://railway.app) → **New Project** → **Deploy from
     GitHub repo** → seleziona questo repository.

2. **Aggiungi Postgres**
   - Nel progetto → **New** → **Database** → **PostgreSQL**. Railway
     genera ed espone `DATABASE_URL` a tutti i servizi del progetto che la
     referenziano.

3. **Servizio backend (web)**
   - **New** → **GitHub Repo** → stesso repo → **Root Directory**:
     `backend`. Railway rileva `railway.json` e il `Dockerfile`.
   - **Variables**: aggiungi tutte quelle di `.env.example` per il backend
     (`SECRET_KEY`, `DASHBOARD_ADMIN_EMAIL`, `DASHBOARD_ADMIN_PASSWORD`,
     `APOLLO_API_KEY`, `ANTHROPIC_API_KEY`, `MS_GRAPH_*`,
     `EMAIL_DRY_RUN`, `MAX_EMAILS_PER_DAY`, `UNSUBSCRIBE_BASE_URL`,
     `FRONTEND_ORIGIN`, `ENVIRONMENT=production`). **`DATABASE_URL` è
     obbligatoria** (senza, il backend prova a connettersi a
     `localhost:5432` e va in crash loop): imposta un riferimento alla
     variabile del servizio Postgres, in Railway digitando
     `${{Postgres.DATABASE_URL}}` nel valore della variabile (menu "Add
     Reference" nell'editor delle Variables). Lo schema `postgres://` /
     `postgresql://` che Railway espone viene normalizzato automaticamente
     dal codice in `postgresql+psycopg://`, non serve modificarlo a mano.
   - **Settings → Networking** → genera un dominio pubblico (serve per
     `UNSUBSCRIBE_BASE_URL` e per l'URL che userà il frontend).
   - Il comando di avvio in `railway.json` esegue `alembic upgrade head`
     automaticamente prima di avviare il server ad ogni deploy.

4. **Servizio frontend (web)**
   - **New** → stesso repo → **Root Directory**: `frontend`.
   - **Variables** → **Build Variables** (non runtime, perché Next.js le
     inietta nel bundle in fase di build): `NEXT_PUBLIC_API_BASE_URL` =
     l'URL pubblico del servizio backend generato al punto 3.
   - **Settings → Networking** → genera un dominio pubblico: è l'indirizzo
     della dashboard.
   - Torna al servizio backend e aggiorna `FRONTEND_ORIGIN` con questo
     dominio (serve per il CORS in produzione).

5. **Servizio cron: job settimanale**
   - **New** → stesso repo → **Root Directory**: `backend` di nuovo (stesso
     codice, servizio separato).
   - **Settings → Deploy** → **Custom Start Command**:
     `python -m app.jobs.weekly_job`.
   - **Settings → Cron Schedule**: `0 * * * *` (ogni ora — vedi sopra
     perché l'orario effettivo si configura da dashboard, non qui).
   - Stesse **Variables** del backend (Railway permette di copiarle da un
     altro servizio). Nessun dominio pubblico necessario.

6. **Servizio cron: job giornaliero**
   - Come il punto 5, ma **Custom Start Command**:
     `python -m app.jobs.daily_job`.

7. **Primo accesso**
   - Apri il dominio del frontend → `/login` → credenziali
     `DASHBOARD_ADMIN_EMAIL` / `DASHBOARD_ADMIN_PASSWORD`.
   - Dalla pagina **Impostazioni** imposta giorno/ora reali per i job.

### Problemi comuni al primo deploy

- **Il backend va in crash loop con `Connection refused` su
  `127.0.0.1:5432`**: manca `DATABASE_URL` su quel servizio (backend o uno
  dei due cron), quindi il codice usa il default per lo sviluppo locale.
  Vai su quel servizio → **Variables** → aggiungi `DATABASE_URL` con il
  riferimento al servizio Postgres (`${{Postgres.DATABASE_URL}}`). Ricorda:
  **tutti e tre** i servizi basati su `backend/` (web + 2 cron) hanno
  bisogno di questa variabile, non solo il web.
- **Il frontend mostra errori di rete verso `localhost:8000`**: il build
  del frontend non ha ricevuto `NEXT_PUBLIC_API_BASE_URL` come *build
  variable* (Railway: sezione "Build Variables" nelle Variables del
  servizio frontend, non quelle runtime). Dopo averla aggiunta serve un
  nuovo deploy (redeploy), perché il valore viene inglobato nel bundle in
  fase di build, non letto a runtime.
- **`/login` risponde 401 anche con le credenziali giuste**: il backend
  non è riuscito a fare il seed dell'utente admin all'avvio (di solito
  perché il DB non era ancora raggiungibile in quel momento) — riavvia il
  servizio backend dopo aver sistemato `DATABASE_URL`.

### Alternativa: Render

Se preferisci Render invece di Railway: backend e frontend come **Web
Service** (Docker, stesso `Dockerfile`/root directory), i due job come
risorse **Cron Job** (non Web Service) con **Command**:
`python -m app.jobs.weekly_job` / `daily_job` e **Schedule**: `0 * * * *`,
tutti collegati allo stesso Postgres tramite `DATABASE_URL`. Vale la stessa
nota sul build-time per `NEXT_PUBLIC_API_BASE_URL` nel servizio frontend.

## Compliance (GDPR)

- Ogni lead ha un campo `legal_basis` valorizzato di default con la base
  giuridica standard (legittimo interesse B2B, art. 6.1.f GDPR).
- La tabella `suppressions` è una lista globale e permanente di opt-out,
  indipendente dai singoli lead/campagne: un indirizzo che si disiscrive non
  può essere ricontattato in nessuna campagna futura, anche se il lead
  originale viene cancellato.
- Cancellazione di un lead = diritto all'oblio, gestita a livello applicativo
  nella Fase 5/7.
