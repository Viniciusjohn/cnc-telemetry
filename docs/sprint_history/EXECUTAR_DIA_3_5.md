# 🚀 DIA 3-5: F5 Histórico TimescaleDB — Guia de Execução

**Objetivo:** Implementar histórico de 30 dias com queries rápidas (<2s)  
**Prazo:** 7-9 Nov (3 dias)  
**Status:** 🏃 EM ANDAMENTO

---

## ⚙️ PASSO 1: Instalar PostgreSQL + TimescaleDB (30 min)

### Opção A: Script Automatizado (Recomendado)
```bash
./scripts/install_timescaledb.sh
```

### Opção B: Manual (se script falhar)
```bash
# 1. Verificar se PostgreSQL já está instalado
psql --version

# Se não estiver instalado:
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15

# 2. Adicionar repositório TimescaleDB
sudo sh -c "echo 'deb [signed-by=/usr/share/keyrings/timescale.keyring] https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"

wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | gpg --dearmor | sudo tee /usr/share/keyrings/timescale.keyring >/dev/null

# 3. Instalar TimescaleDB
sudo apt update
sudo apt install -y timescaledb-2-postgresql-15

# 4. Configurar TimescaleDB
sudo timescaledb-tune --quiet --yes

# 5. Restart PostgreSQL
sudo systemctl restart postgresql

# 6. Verificar status
sudo systemctl status postgresql
```

---

## 🗄️ PASSO 2: Criar Database e Usuário (5 min)

```bash
# Criar database
sudo -u postgres psql -c "CREATE DATABASE cnc_telemetry;"

# Habilitar TimescaleDB extension
sudo -u postgres psql -d cnc_telemetry -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Criar usuário
sudo -u postgres psql -c "CREATE USER cnc_user WITH PASSWORD 'cnc_telemetry_2025';"

# Dar permissões
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cnc_telemetry TO cnc_user;"
sudo -u postgres psql -d cnc_telemetry -c "GRANT ALL ON SCHEMA public TO cnc_user;"

# Testar conexão
psql -U cnc_user -d cnc_telemetry -c "SELECT version();"
# Senha: cnc_telemetry_2025
```

---

## 📄 PASSO 3: Aplicar Schemas SQL (10 min)

```bash
# Schema principal (hypertable + índices)
psql -U cnc_user -d cnc_telemetry -f backend/db/schema.sql
# Senha: cnc_telemetry_2025

# Continuous aggregates (5m, 1h, 1d)
psql -U cnc_user -d cnc_telemetry -f backend/db/aggregates.sql

# OEE schema
psql -U cnc_user -d cnc_telemetry -f backend/db/oee_schema.sql

# Verificar tabelas criadas
psql -U cnc_user -d cnc_telemetry -c "\dt"
```

**Esperado:**
```
           List of relations
 Schema |      Name       | Type  |   Owner   
--------+-----------------+-------+-----------
 public | oee_daily       | table | cnc_user
 public | telemetry       | table | cnc_user
```

---

## 🐍 PASSO 4: Instalar Dependências Python (5 min)

```bash
cd backend
source .venv/bin/activate

# Instalar drivers PostgreSQL + SQLAlchemy
pip install psycopg2-binary==2.9.9
pip install asyncpg==0.29.0
pip install sqlalchemy==2.0.23
pip install alembic==1.13.0

# Atualizar requirements.txt
pip freeze > requirements.txt
```

---

## 🔧 PASSO 5: Configurar .env (2 min)

```bash
# Criar/editar backend/.env
cat > backend/.env << 'EOF'
# Database
DATABASE_URL=postgresql://cnc_user:cnc_telemetry_2025@localhost/cnc_telemetry

# API
API_BASE=http://localhost:8001
ENVIRONMENT=development

# MTConnect
MTCONNECT_AGENT_URL=http://localhost:5000
MACHINE_ID=CNC-SIM-001

# Alertas (opcional agora, necessário no DIA 6-7)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF

echo "✅ .env criado"
```

---

## ⚡ PASSO 6: Testar Conexão DB no Python (5 min)

```bash
# Testar ORM models
cd backend
python3 app/db.py

# Esperado:
# ✅ Database connected: PostgreSQL 15.x with TimescaleDB
```

Se der erro:
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar se usuário/senha estão corretos
psql -U cnc_user -d cnc_telemetry -c "SELECT 1;"
```

---

## 🛠️ PASSO 7: Modificar /ingest para Gravar no DB (30 min)

### Editar `backend/main.py` (ou `app.py`)

Adicionar import:
```python
from app.db import get_db, Telemetry
from sqlalchemy.orm import Session
from fastapi import Depends
```

Modificar endpoint `/v1/telemetry/ingest`:
```python
@app.post("/v1/telemetry/ingest", status_code=201)
async def ingest_telemetry(
    payload: TelemetryPayload,
    db: Session = Depends(get_db)
):
    # Parse timestamp
    ts = datetime.fromisoformat(payload.timestamp.replace('Z', '+00:00'))
    
    # Salvar no TimescaleDB
    db_record = Telemetry(
        ts=ts,
        machine_id=payload.machine_id,
        rpm=payload.rpm,
        feed_mm_min=payload.feed_mm_min,
        state=payload.state,
        sequence=getattr(payload, 'sequence', None)
    )
    db.add(db_record)
    db.commit()
    
    # Atualizar status em memória (para /status)
    update_status(
        machine_id=payload.machine_id,
        rpm=payload.rpm,
        feed_mm_min=payload.feed_mm_min,
        state=payload.state
    )
    
    return {
        "ingested": True,
        "machine_id": payload.machine_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
```

---

## 📊 PASSO 8: Criar Router /history (45 min)

Arquivo já criado: `backend/app/routers/history.py`

Criar o arquivo:
```python
# backend/app/routers/history.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Optional

from ..db import get_db

router = APIRouter(prefix="/v1/machines", tags=["history"])

@router.get("/{machine_id}/history")
def get_history(
    machine_id: str,
    from_ts: str = Query(..., description="ISO 8601 timestamp"),
    to_ts: str = Query(..., description="ISO 8601 timestamp"),
    resolution: str = Query("5m", description="raw | 5m | 1h | 1d"),
    db: Session = Depends(get_db)
):
    """
    Get historical telemetry data.
    
    Example:
        GET /v1/machines/CNC-SIM-001/history?from_ts=2025-10-05T00:00:00Z&to_ts=2025-11-05T00:00:00Z&resolution=1h
    """
    # Parse timestamps
    from_dt = datetime.fromisoformat(from_ts.replace('Z', '+00:00'))
    to_dt = datetime.fromisoformat(to_ts.replace('Z', '+00:00'))
    
    # Selecionar tabela baseado na resolução
    if resolution == "raw":
        query = text("""
            SELECT ts, machine_id, rpm, feed_mm_min, state, sequence
            FROM telemetry
            WHERE machine_id = :machine_id
              AND ts >= :from_ts
              AND ts <= :to_ts
            ORDER BY ts DESC
            LIMIT 10000
        """)
    elif resolution == "5m":
        query = text("""
            SELECT bucket AS ts, machine_id, 
                   rpm_avg AS rpm, feed_avg AS feed_mm_min, 
                   state_mode AS state, sample_count
            FROM telemetry_5m
            WHERE machine_id = :machine_id
              AND bucket >= :from_ts
              AND bucket <= :to_ts
            ORDER BY bucket DESC
            LIMIT 10000
        """)
    elif resolution == "1h":
        query = text("""
            SELECT bucket AS ts, machine_id, 
                   rpm_avg AS rpm, feed_avg AS feed_mm_min, sample_count
            FROM telemetry_1h
            WHERE machine_id = :machine_id
              AND bucket >= :from_ts
              AND bucket <= :to_ts
            ORDER BY bucket DESC
        """)
    elif resolution == "1d":
        query = text("""
            SELECT date AS ts, machine_id, 
                   rpm_avg AS rpm, feed_avg AS feed_mm_min, 
                   availability, sample_count
            FROM telemetry_1d
            WHERE machine_id = :machine_id
              AND date >= :from_ts::date
              AND date <= :to_ts::date
            ORDER BY date DESC
        """)
    else:
        raise HTTPException(status_code=400, detail="Invalid resolution")
    
    # Execute query
    result = db.execute(query, {
        "machine_id": machine_id,
        "from_ts": from_dt,
        "to_ts": to_dt
    })
    
    # Format response
    rows = []
    for row in result:
        rows.append({
            "ts": row.ts.isoformat(),
            "machine_id": row.machine_id,
            "rpm": float(row.rpm) if row.rpm else 0,
            "feed_mm_min": float(row.feed_mm_min) if hasattr(row, 'feed_mm_min') else 0,
            "state": row.state if hasattr(row, 'state') else None,
        })
    
    return {
        "machine_id": machine_id,
        "from_ts": from_ts,
        "to_ts": to_ts,
        "resolution": resolution,
        "count": len(rows),
        "data": rows
    }
```

Wire no `main.py`:
```python
from app.routers import history

app.include_router(history.router)
```

---

## 🧪 PASSO 9: Testar Ingestão e Query (15 min)

### 9.1 Testar Ingestão
```bash
# Rodar backend
cd backend
source .venv/bin/activate
uvicorn main:app --port 8001 --reload

# Em outro terminal, enviar dados
curl -X POST http://localhost:8001/v1/telemetry/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "machine_id": "TEST-001",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "rpm": 4500,
    "feed_mm_min": 1200,
    "state": "running"
  }'

# Verificar no DB
psql -U cnc_user -d cnc_telemetry -c "SELECT * FROM telemetry ORDER BY ts DESC LIMIT 5;"
```

### 9.2 Testar Histórico
```bash
# Query raw data (últimas 24h)
curl "http://localhost:8001/v1/machines/TEST-001/history?from_ts=$(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%SZ)&to_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)&resolution=raw" | jq

# Query aggregated (5 min)
curl "http://localhost:8001/v1/machines/TEST-001/history?from_ts=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)&to_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)&resolution=5m" | jq
```

---

## ✅ PASSO 10: Validar Performance (15 min)

### 10.1 Load Test (Ingestão)
```bash
# Enviar 5000 pontos em 1 minuto
for i in {1..5000}; do
  curl -s -X POST http://localhost:8001/v1/telemetry/ingest \
    -H 'Content-Type: application/json' \
    -d "{\"machine_id\":\"LOAD-TEST\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\",\"rpm\":$((RANDOM%5000)),\"feed_mm_min\":$((RANDOM%2000)),\"state\":\"running\"}" &
  
  # Rate limit (83 req/s)
  if (( i % 83 == 0 )); then
    sleep 1
  fi
done
wait

echo "✅ Load test completo"
```

### 10.2 Query Performance (P95 < 2s)
```bash
# Medir tempo de query 30 dias
time curl -s "http://localhost:8001/v1/machines/LOAD-TEST/history?from_ts=$(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ)&to_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)&resolution=1h" | jq 'length'

# Esperado: real < 2.0s
```

### 10.3 Database Query Performance
```sql
-- Query direta no PostgreSQL
psql -U cnc_user -d cnc_telemetry

EXPLAIN ANALYZE 
SELECT bucket, machine_id, rpm_avg, feed_avg
FROM telemetry_1h
WHERE machine_id = 'LOAD-TEST'
  AND bucket > NOW() - INTERVAL '30 days'
ORDER BY bucket DESC;

-- Verificar: Execution Time < 200ms
```

---

## 📊 Critérios de Aceite F5

- [ ] PostgreSQL 15 + TimescaleDB instalado
- [ ] Database `cnc_telemetry` criado
- [ ] Schemas aplicados (hypertable + aggregates)
- [ ] `/ingest` grava no TimescaleDB
- [ ] `/history` endpoint funciona
- [ ] Query P95 < 2s (30 dias, resolution=1h)
- [ ] Ingestão ≥ 5000 pontos/min
- [ ] Compression ativa após 7 dias
- [ ] Retention 30 dias ativo

---

## 🐛 Troubleshooting

### Erro: "role cnc_user does not exist"
```bash
sudo -u postgres psql -c "CREATE USER cnc_user WITH PASSWORD 'cnc_telemetry_2025';"
```

### Erro: "database cnc_telemetry does not exist"
```bash
sudo -u postgres psql -c "CREATE DATABASE cnc_telemetry;"
```

### Erro: "extension timescaledb does not exist"
```bash
# Reinstalar TimescaleDB
sudo apt install timescaledb-2-postgresql-15
sudo timescaledb-tune
sudo systemctl restart postgresql
```

### Query muito lenta
```sql
-- Verificar se índices estão criados
\d telemetry

-- Verificar se hypertable está ativa
SELECT * FROM timescaledb_information.hypertables;

-- Forçar VACUUM
VACUUM ANALYZE telemetry;
```

---

## 📝 Checklist de Execução

- [ ] PASSO 1: Instalar PostgreSQL + TimescaleDB
- [ ] PASSO 2: Criar database e usuário
- [ ] PASSO 3: Aplicar schemas SQL
- [ ] PASSO 4: Instalar deps Python
- [ ] PASSO 5: Configurar .env
- [ ] PASSO 6: Testar conexão DB
- [ ] PASSO 7: Modificar /ingest
- [ ] PASSO 8: Criar router /history
- [ ] PASSO 9: Testar ingestão e query
- [ ] PASSO 10: Validar performance

---

**Tempo Estimado Total:** 2-3 horas  
**Próximo:** DIA 6-7 (F6 Alertas)
