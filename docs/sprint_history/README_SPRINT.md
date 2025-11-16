# 🚀 CNC Telemetry — Sprint 11 Dias

**Objetivo:** PMV pronto para fechar primeiro cliente  
**Prazo:** 5-15 Nov 2025  
**Status:** 🏃 Em andamento

---

## 📊 Progress do Sprint

```
✅ DIA 1-2: F3 Gate Final (Playwright + Screenshots)
✅ DIA 3-5: F5 Histórico TimescaleDB (Code completo)
✅ DIA 6-7: F6 Alertas (Celery + Slack) (Code completo)
🔜 DIA 8-10: F8 OEE (Dashboard + CSV Export)
🔜 DIA 11: PoC Package (Relatório + Proposta)
```

**Overall:** 55% (6/11 dias de código)

---

## 🎯 Guias de Execução

Cada fase tem um guia detalhado passo-a-passo:

1. **`EXECUTAR_DIA_3_5.md`** — F5 Histórico TimescaleDB
   - Instalar PostgreSQL + TimescaleDB
   - Aplicar schemas SQL
   - Configurar backend
   - Testar queries (<2s)

2. **`EXECUTAR_DIA_6_7.md`** — F6 Alertas
   - Instalar Redis
   - Configurar Slack webhook
   - Rodar Celery worker + beat
   - Testar alertas (<5s latência)

3. **`TODO_SPRINT_11_DIAS.md`** — Checklist completo
   - TODOs detalhados por dia
   - Tracking progress
   - Critérios de aceite

---

## ⚡ Quick Start (Local Development)

### 1. Backend (API + Adapter)

```bash
cd backend

# Criar venv
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cat > .env << 'EOF'
DATABASE_URL=postgresql://cnc_user:cnc_telemetry_2025@localhost/cnc_telemetry
REDIS_URL=redis://localhost:6379/0
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
MTCONNECT_AGENT_URL=http://localhost:5000
EOF

# Rodar API
uvicorn main:app --port 8001 --reload
```

### 2. Frontend (Dashboard PWA)

```bash
cd frontend

# Instalar dependências
npm install

# Rodar dev server
npm run dev
# Acesso: http://localhost:5173
```

### 3. MTConnect Simulator

```bash
# Instalar dependências
pip install fastapi uvicorn

# Rodar simulador
python3 scripts/mtconnect_simulator.py --port 5000
# Acesso: http://localhost:5000/current
```

### 4. Celery (Alertas)

```bash
cd backend
source .venv/bin/activate

# Terminal 1: Worker
celery -A app.services.alerts:celery_app worker --loglevel=info

# Terminal 2: Beat (scheduler)
celery -A app.services.alerts:celery_app beat --loglevel=info
```

---

## 🗄️ Setup Database (PostgreSQL + TimescaleDB)

```bash
# Instalar
./scripts/install_timescaledb.sh

# Aplicar schemas
psql -U cnc_user -d cnc_telemetry -f backend/db/schema.sql
psql -U cnc_user -d cnc_telemetry -f backend/db/aggregates.sql
psql -U cnc_user -d cnc_telemetry -f backend/db/oee_schema.sql
```

**Ver:** `EXECUTAR_DIA_3_5.md` para detalhes completos

---

## 🧪 Testes

### Playwright E2E (Frontend)

```bash
cd frontend

# Instalar Playwright
npm install -D @playwright/test
npx playwright install

# Rodar testes
npx playwright test

# Ver relatório
npx playwright show-report
```

### Smoke Tests (Backend)

```bash
cd scripts

# Rodar smoke tests
./smoke_f3.sh

# Ver resultados
cat /tmp/smoke_f3_*.log
```

---

## 📦 Arquitetura

```
┌─────────────────┐
│  MTConnect CNC  │
│   (Simulator)   │
│   :5000         │
└────────┬────────┘
         │
         ↓ HTTP /sample
┌────────────────────────┐
│  MTConnect Adapter     │
│  (Python)              │
│  - Poll a cada 2s      │
│  - Normalizar estados  │
└───────────┬────────────┘
            │
            ↓ POST /ingest
┌────────────────────────────────────┐
│         FastAPI Backend            │
│         :8001                      │
│                                    │
│  /v1/telemetry/ingest             │
│  /v1/machines/{id}/status         │
│  /v1/machines/{id}/history        │
│  /v1/machines/{id}/oee            │
└────┬───────────────────────────┬───┘
     │                           │
     ↓                           ↓
┌──────────────┐         ┌─────────────┐
│ PostgreSQL + │         │   Redis     │
│ TimescaleDB  │         │   :6379     │
│              │         │             │
│ - Hypertable │         │ - Dedupe    │
│ - Aggregates │         │ - Sessions  │
│ - Retention  │         │             │
└──────────────┘         └─────────────┘
     ↑                           ↑
     │                           │
┌────┴────────────────────────┴───┐
│     Celery Worker + Beat        │
│     (Alertas)                   │
│     - Evalua a cada 30s         │
│     - Dedupe 60s                │
│     - Slack webhook             │
└─────────────────────────────────┘
     │
     ↓ Slack API
┌─────────────────┐
│  Slack Channel  │
│  #cnc-alerts    │
└─────────────────┘

┌─────────────────┐
│  React PWA      │
│  :5173          │
│                 │
│  - Dashboard    │
│  - Polling 2s   │
│  - Gráficos     │
└─────────────────┘
```

---

## 📁 Estrutura do Projeto

```
cnc-telemetry/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── status.py       # Status real-time
│   │   │   ├── history.py      # Histórico (F5)
│   │   │   └── oee.py          # OEE cálculo (F8)
│   │   ├── services/
│   │   │   ├── alerts.py       # Celery alertas (F6)
│   │   │   └── oee.py          # OEE business logic
│   │   └── db.py               # SQLAlchemy models
│   ├── db/
│   │   ├── schema.sql          # Hypertable + índices
│   │   ├── aggregates.sql      # Continuous aggregates
│   │   └── oee_schema.sql      # OEE table
│   ├── main.py                 # FastAPI app
│   ├── mtconnect_adapter.py    # Adapter MTConnect
│   └── requirements.txt        # Dependências Python
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Dashboard React
│   │   └── lib/
│   │       └── api.ts          # API client
│   ├── tests/
│   │   └── smoke.spec.ts       # Playwright E2E
│   ├── playwright.config.ts
│   └── package.json
│
├── config/
│   └── alerts.yaml             # Regras de alertas
│
├── scripts/
│   ├── mtconnect_simulator.py  # Simulador CNC
│   ├── install_timescaledb.sh  # Setup DB
│   ├── capture_screenshots.ts  # Screenshots
│   └── smoke_f3.sh             # Smoke tests
│
├── docs/
│   ├── F3_GATE_FINAL_REPORT.md # Relatório F3
│   ├── COMPETITIVE_ANALYSIS.md # Análise concorrentes
│   ├── PMV_PRIMEIRO_CLIENTE.md # PMV definition
│   ├── PROPOSTA_COMERCIAL.md   # Proposta template
│   └── screenshots/            # UI screenshots
│
├── EXECUTAR_DIA_3_5.md         # Guia F5 (Histórico)
├── EXECUTAR_DIA_6_7.md         # Guia F6 (Alertas)
└── TODO_SPRINT_11_DIAS.md      # Checklist completo
```

---

## 🎯 APIs Disponíveis

### Status Real-Time
```bash
GET /v1/machines/{machine_id}/status
```

### Histórico
```bash
GET /v1/machines/{machine_id}/history?from_ts=...&to_ts=...&resolution=5m
GET /v1/machines/{machine_id}/history/summary?from_ts=...&to_ts=...
```

### OEE
```bash
GET /v1/machines/{machine_id}/oee?date=2025-11-05&shift=daily
GET /v1/machines/{machine_id}/oee/trend?from_date=...&to_date=...
GET /v1/machines/{machine_id}/oee/export?format=csv
```

### Ingestão
```bash
POST /v1/telemetry/ingest
{
  "machine_id": "CNC-001",
  "timestamp": "2025-11-05T10:30:00Z",
  "rpm": 4500,
  "feed_mm_min": 1200,
  "state": "running"
}
```

---

## 🐛 Troubleshooting

### Backend não inicia
```bash
# Verificar Python version
python3 --version  # Deve ser >= 3.10

# Recriar venv
rm -rf backend/.venv
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

### Frontend não compila
```bash
# Limpar node_modules
rm -rf frontend/node_modules frontend/package-lock.json
npm install
```

### Database connection error
```bash
# Verificar PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar usuário/senha
psql -U cnc_user -d cnc_telemetry -c "SELECT 1;"
```

### Alertas não disparam
```bash
# Verificar Redis
redis-cli ping

# Verificar Celery worker está rodando
ps aux | grep celery

# Ver logs
celery -A app.services.alerts:celery_app inspect active
```

---

## 📚 Documentação Adicional

- **F3 Gate:** `docs/F3_GATE_FINAL_REPORT.md`
- **Análise Competitiva:** `docs/COMPETITIVE_ANALYSIS.md`
- **Pitch:** `docs/PITCH_DIFERENCIAIS.md`
- **PMV:** `docs/PMV_PRIMEIRO_CLIENTE.md`
- **Roadmap:** `docs/ROADMAP_EXECUTIVO.md`

---

## 🚀 Deploy (Produção)

Ver systemd services em `EXECUTAR_DIA_6_7.md` para:
- Celery worker (alertas)
- Celery beat (scheduler)

---

## 📞 Suporte

**Issues:** https://github.com/Viniciusjohn/cnc-telemetry/issues  
**Docs:** https://github.com/Viniciusjohn/cnc-telemetry/tree/main/docs

---

**Versão:** 1.0  
**Última Atualização:** 2025-11-05
