# 🚀 TODO Sprint 11 Dias — Fechar PMV

**Início:** 05/Nov/2025  
**Fim:** 15/Nov/2025  
**Objetivo:** PMV pronto para vender

---

## 📅 DIA 1-2 (5-6 Nov): F3 Gate Final

### TODO 1.1: Playwright Smoke Tests
- [ ] Instalar Playwright no frontend
  ```bash
  cd frontend
  npm install -D @playwright/test
  npx playwright install
  ```
- [ ] Criar `frontend/tests/smoke.spec.ts`
  - [ ] Test: Dashboard loads
  - [ ] Test: Cards são visíveis
  - [ ] Test: Polling funciona (wait 5s, check update)
  - [ ] Test: Sem erros console
- [ ] Rodar testes
  ```bash
  npx playwright test
  ```
- [ ] Gerar relatório HTML
  ```bash
  npx playwright show-report
  ```

### TODO 1.2: Screenshots
- [ ] Dashboard desktop (1920x1080)
  - [ ] Estado: Running (verde)
  - [ ] Estado: Stopped (vermelho)
  - [ ] Estado: Idle (amarelo)
- [ ] Dashboard mobile (375x667)
  - [ ] Responsividade OK
  - [ ] Cards empilhados verticalmente
- [ ] Salvar em `docs/screenshots/`
  - [ ] `dashboard-desktop-running.png`
  - [ ] `dashboard-desktop-stopped.png`
  - [ ] `dashboard-mobile.png`

### TODO 1.3: Documentar F3 PASS
- [ ] Preencher `docs/F3_GATE_UNICO.md`
  - [ ] G1: Headers ✓
  - [ ] G2: JSON schema ✓
  - [ ] G3: CORS ✓
  - [ ] G4: MTConnect ✓
  - [ ] G5: UI ✓
  - [ ] G6: Playwright ✓
- [ ] Commit: "F3 PASS: Dashboard PWA validado"
- [ ] Anexar na issue #4

---

## 📅 DIA 3-5 (7-9 Nov): F5 Histórico TimescaleDB

### TODO 2.1: Instalar PostgreSQL + TimescaleDB
- [ ] Instalar PostgreSQL 15
  ```bash
  sudo apt update
  sudo apt install -y postgresql-15 postgresql-contrib-15
  ```
- [ ] Instalar TimescaleDB
  ```bash
  sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
  wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
  sudo apt update
  sudo apt install -y timescaledb-2-postgresql-15
  ```
- [ ] Configurar TimescaleDB
  ```bash
  sudo timescaledb-tune --quiet --yes
  sudo systemctl restart postgresql
  ```
- [ ] Criar database
  ```bash
  sudo -u postgres psql -c "CREATE DATABASE cnc_telemetry;"
  sudo -u postgres psql -d cnc_telemetry -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
  sudo -u postgres psql -c "CREATE USER cnc_user WITH PASSWORD 'strong_password_here';"
  sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cnc_telemetry TO cnc_user;"
  ```

### TODO 2.2: Schema + Hypertable
- [ ] Criar `backend/db/schema.sql`
  ```sql
  CREATE TABLE telemetry (
    ts TIMESTAMPTZ NOT NULL,
    machine_id TEXT NOT NULL,
    rpm DOUBLE PRECISION CHECK (rpm >= 0),
    feed_mm_min DOUBLE PRECISION CHECK (feed_mm_min >= 0),
    state TEXT CHECK (state IN ('running','stopped','idle')),
    sequence BIGINT,
    src TEXT DEFAULT 'mtconnect',
    ingested_at TIMESTAMPTZ DEFAULT NOW()
  );
  
  SELECT create_hypertable('telemetry', 'ts', if_not_exists=>TRUE);
  
  CREATE INDEX idx_machine_ts ON telemetry(machine_id, ts DESC);
  CREATE INDEX idx_state_ts ON telemetry(state, ts DESC) WHERE state != 'idle';
  CREATE INDEX idx_sequence ON telemetry(sequence) WHERE sequence IS NOT NULL;
  ```
- [ ] Executar schema
  ```bash
  psql -U cnc_user -d cnc_telemetry -f backend/db/schema.sql
  ```

### TODO 2.3: Retention Policy
- [ ] Adicionar ao schema.sql
  ```sql
  SELECT add_retention_policy('telemetry', INTERVAL '30 days', if_not_exists=>TRUE);
  ```
- [ ] Executar

### TODO 2.4: Continuous Aggregates
- [ ] Criar `backend/db/aggregates.sql`
  ```sql
  -- 5 minutos
  CREATE MATERIALIZED VIEW telemetry_5m
  WITH (timescaledb.continuous) AS
    SELECT 
      time_bucket('5 minutes', ts) AS bucket,
      machine_id,
      AVG(rpm) AS rpm_avg,
      MAX(rpm) AS rpm_max,
      MIN(rpm) AS rpm_min,
      STDDEV(rpm) AS rpm_stddev,
      AVG(feed_mm_min) AS feed_avg,
      MAX(feed_mm_min) AS feed_max,
      COUNT(*) AS sample_count,
      MODE() WITHIN GROUP (ORDER BY state) AS state_mode
    FROM telemetry
    GROUP BY bucket, machine_id
    WITH NO DATA;
  
  SELECT add_continuous_aggregate_policy('telemetry_5m',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE);
  
  -- 1 hora
  CREATE MATERIALIZED VIEW telemetry_1h
  WITH (timescaledb.continuous) AS
    SELECT 
      time_bucket('1 hour', bucket) AS bucket,
      machine_id,
      AVG(rpm_avg) AS rpm_avg,
      MAX(rpm_max) AS rpm_max,
      AVG(feed_avg) AS feed_avg,
      SUM(sample_count) AS sample_count
    FROM telemetry_5m
    GROUP BY 1, 2
    WITH NO DATA;
  
  SELECT add_continuous_aggregate_policy('telemetry_1h',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);
  ```
- [ ] Executar
  ```bash
  psql -U cnc_user -d cnc_telemetry -f backend/db/aggregates.sql
  ```

### TODO 2.5: Backend Integration
- [ ] Instalar dependências
  ```bash
  cd backend
  source .venv/bin/activate
  pip install psycopg2-binary asyncpg sqlalchemy alembic
  ```
- [ ] Atualizar `requirements.txt`
- [ ] Criar `backend/app/db.py` (ORM models)
- [ ] Modificar `/v1/telemetry/ingest` para gravar no DB
- [ ] Testar ingestão

### TODO 2.6: Endpoint /history
- [ ] Criar `backend/app/routers/history.py`
- [ ] Endpoint GET `/v1/machines/{id}/history`
  - Query params: `from_ts`, `to_ts`, `resolution` (raw/5m/1h/1d)
- [ ] Wire no `main.py`
- [ ] Testar
  ```bash
  curl "http://localhost:8001/v1/machines/CNC-SIM-001/history?from_ts=2025-10-05T00:00:00Z&to_ts=2025-11-05T00:00:00Z&resolution=1h" | jq
  ```

### TODO 2.7: Validar Query Performance
- [ ] Load test (5000 pontos em 1 min)
- [ ] Query P95 < 2s
  ```sql
  EXPLAIN ANALYZE 
  SELECT * FROM telemetry_1h 
  WHERE machine_id='CNC-SIM-001' 
    AND bucket > NOW() - INTERVAL '30 days';
  ```
- [ ] Documentar resultados

---

## 📅 DIA 6-7 (10-11 Nov): F6 Alertas

### TODO 3.1: Setup Celery + Redis
- [ ] Instalar Redis
  ```bash
  sudo apt install -y redis-server
  sudo systemctl start redis
  sudo systemctl enable redis
  ```
- [ ] Instalar dependências Python
  ```bash
  pip install celery redis pyyaml httpx
  ```
- [ ] Atualizar `requirements.txt`

### TODO 3.2: Engine de Alertas
- [ ] Criar `backend/app/services/alerts.py`
  - [ ] Celery app config
  - [ ] Task `evaluate_alerts()`
  - [ ] Função `load_rules()`
  - [ ] Função `eval_condition()`
  - [ ] Função `send_alert()`
  - [ ] Dedupe logic (Redis cache)
- [ ] Criar `backend/celerybeat_config.py`
  - [ ] Beat schedule (a cada 30s)

### TODO 3.3: Config de Regras
- [ ] Criar `config/alerts.yaml`
  ```yaml
  alerts:
    - name: machine_stopped_long
      machine_id: "*"
      condition: "state == 'stopped' AND duration_seconds > 60"
      severity: warning
      channels:
        - type: slack
          webhook: ${SLACK_WEBHOOK_URL}
          
    - name: execution_no_movement
      machine_id: "*"
      condition: "rpm == 0 AND state == 'running'"
      severity: critical
      duration_seconds: 60
      channels:
        - type: slack
          webhook: ${SLACK_WEBHOOK_URL}
  ```
- [ ] Configurar variável ambiente `SLACK_WEBHOOK_URL`

### TODO 3.4: Rodar Celery
- [ ] Terminal 1: Worker
  ```bash
  cd backend
  celery -A app.services.alerts worker --loglevel=info
  ```
- [ ] Terminal 2: Beat (scheduler)
  ```bash
  celery -A app.services.alerts beat --loglevel=info
  ```

### TODO 3.5: Validar Latência < 5s
- [ ] Simular condição (máquina parada)
- [ ] Medir tempo até alerta Slack
- [ ] Documentar resultado
- [ ] Verificar dedupe (1 alerta/min)

---

## 📅 DIA 8-10 (12-14 Nov): F8 OEE Básico

### TODO 4.1: Schema OEE
- [ ] Criar `backend/db/oee_schema.sql`
  ```sql
  CREATE TABLE oee_daily (
    date DATE NOT NULL,
    machine_id TEXT NOT NULL,
    shift TEXT CHECK (shift IN ('morning','afternoon','night')),
    planned_time_min INT NOT NULL,
    operating_time_min INT NOT NULL,
    availability FLOAT,
    performance FLOAT DEFAULT 1.0,
    quality FLOAT DEFAULT 1.0,
    oee FLOAT,
    PRIMARY KEY (date, machine_id, shift)
  );
  
  CREATE INDEX idx_oee_date ON oee_daily(date DESC);
  CREATE INDEX idx_oee_machine ON oee_daily(machine_id, date DESC);
  ```
- [ ] Executar
  ```bash
  psql -U cnc_user -d cnc_telemetry -f backend/db/oee_schema.sql
  ```

### TODO 4.2: Função calculate_oee()
- [ ] Criar `backend/app/services/oee.py`
  ```python
  def calculate_oee(machine_id: str, date: str, shift: str):
      # 1. Get shift times
      shift_start, shift_end = get_shift_times(shift)
      
      # 2. Query samples
      samples = query_samples(machine_id, shift_start, shift_end)
      
      # 3. Calculate availability
      planned_time_min = (shift_end - shift_start).seconds / 60
      operating_time_min = sum(1 for s in samples if s.state == 'running') * (2/60)
      availability = operating_time_min / planned_time_min
      
      # 4. Performance (simplificado: 1.0)
      performance = 1.0
      
      # 5. Quality (simplificado: 1.0)
      quality = 1.0
      
      # 6. OEE
      oee = availability * performance * quality
      
      return {
          'date': date,
          'machine_id': machine_id,
          'shift': shift,
          'planned_time_min': planned_time_min,
          'operating_time_min': operating_time_min,
          'availability': availability,
          'performance': performance,
          'quality': quality,
          'oee': oee
      }
  ```
- [ ] Testar função com dados reais

### TODO 4.3: Endpoint /oee
- [ ] Criar `backend/app/routers/oee.py`
- [ ] GET `/v1/machines/{id}/oee?date=YYYY-MM-DD`
- [ ] Wire no `main.py`
- [ ] Testar
  ```bash
  curl "http://localhost:8001/v1/machines/CNC-SIM-001/oee?date=2025-11-05" | jq
  ```

### TODO 4.4: Dashboard OEE Card
- [ ] Modificar `frontend/src/App.tsx`
- [ ] Adicionar card "OEE Hoje"
- [ ] Fetch `/v1/machines/{id}/oee`
- [ ] Display: 72% (colorido: verde >70%, amarelo 60-70%, vermelho <60%)

### TODO 4.5: Gráfico 7 Dias
- [ ] Instalar Chart.js
  ```bash
  cd frontend
  npm install chart.js react-chartjs-2
  ```
- [ ] Componente `<OEEChart />`
- [ ] Line chart: OEE últimos 7 dias
- [ ] Integrar no dashboard

### TODO 4.6: Export CSV/PDF
- [ ] Endpoint `/v1/machines/{id}/oee/export?format=csv&from=&to=`
- [ ] Gerar CSV com pandas
- [ ] (Opcional) PDF com ReportLab
- [ ] Botão "Download CSV" no frontend

---

## 📅 DIA 11 (15 Nov): Pacote PoC

### TODO 5.1: Script generate_poc_report.py
- [ ] Criar `scripts/generate_poc_report.py`
  ```python
  import argparse
  import requests
  from datetime import datetime, timedelta
  
  def generate_poc_report(machine_id, duration_min):
      # 1. Query telemetry últimos X minutos
      end = datetime.now()
      start = end - timedelta(minutes=duration_min)
      
      # 2. Calcular métricas
      # - Tempo executando/parado/idle
      # - RPM médio
      # - Feed médio
      # - Alertas disparados
      
      # 3. Calcular OEE
      
      # 4. Gerar relatório Markdown
      report = f"""
      # Relatório PoC — {machine_id}
      
      **Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
      **Duração:** {duration_min} minutos
      
      ## Métricas
      ...
      
      ## OEE
      ...
      
      ## ROI Projetado
      ...
      """
      
      # 5. Salvar em docs/poc_reports/
      filename = f"poc_{machine_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
      with open(f"docs/poc_reports/{filename}", "w") as f:
          f.write(report)
      
      print(f"✅ Relatório salvo: {filename}")
  
  if __name__ == "__main__":
      parser = argparse.ArgumentParser()
      parser.add_argument("--machine-id", required=True)
      parser.add_argument("--duration", type=int, default=120)
      args = parser.parse_args()
      
      generate_poc_report(args.machine_id, args.duration)
  ```
- [ ] Testar script
  ```bash
  python3 scripts/generate_poc_report.py --machine-id CNC-SIM-001 --duration 120
  ```

### TODO 5.2: Screenshots Automáticos
- [ ] Script Playwright para capturar
  ```typescript
  // scripts/capture_screenshots.ts
  import { chromium } from '@playwright/test';
  
  async function capture() {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    // Desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:5173');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'docs/screenshots/dashboard-desktop.png' });
    
    // Mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.screenshot({ path: 'docs/screenshots/dashboard-mobile.png' });
    
    await browser.close();
  }
  
  capture();
  ```
- [ ] Rodar
  ```bash
  npx ts-node scripts/capture_screenshots.ts
  ```

### TODO 5.3: Proposta Comercial Preenchida
- [ ] Copiar `docs/PROPOSTA_COMERCIAL.md`
- [ ] Preencher:
  - [ ] Nome cliente: Novatech
  - [ ] CNPJ
  - [ ] Data: 15/Nov/2025
  - [ ] Quantidade máquinas: 1 (PoC)
  - [ ] Valor: R$ 99/mês
- [ ] Salvar em `docs/propostas/novatech_2025_11_15.md`
- [ ] Gerar PDF
  ```bash
  pandoc docs/propostas/novatech_2025_11_15.md -o docs/propostas/novatech_2025_11_15.pdf
  ```

### TODO 5.4: Contrato
- [ ] Template contrato em `docs/CONTRATO_TEMPLATE.md`
- [ ] Preencher dados Novatech
- [ ] Salvar em `docs/contratos/novatech_2025_11_15.md`
- [ ] Gerar PDF para assinatura

---

## 🎯 Checklist Final

### Técnico
- [ ] F3 PASS (Playwright + Screenshots)
- [ ] F5 PASS (TimescaleDB + /history)
- [ ] F6 PASS (Alertas <5s)
- [ ] F8 PASS (OEE + Dashboard)

### Comercial
- [ ] Relatório PoC gerado
- [ ] Proposta comercial preenchida
- [ ] Contrato pronto
- [ ] Screenshots anexados

### Deploy
- [ ] Backend rodando (PostgreSQL + Celery)
- [ ] Frontend build produção
- [ ] Adapter conectado à máquina real
- [ ] Slack webhook configurado

---

## 📊 Tracking Progress

| Dia | Fase | Status | Data Conclusão |
|-----|------|--------|----------------|
| 1-2 | F3 Gate | 🔜 | ___/___/___ |
| 3-5 | F5 Histórico | 🔜 | ___/___/___ |
| 6-7 | F6 Alertas | 🔜 | ___/___/___ |
| 8-10 | F8 OEE | 🔜 | ___/___/___ |
| 11 | PoC Package | 🔜 | ___/___/___ |

**Legenda:** 🔜 Pendente | 🏃 Em andamento | ✅ Completo

---

**Última Atualização:** 2025-11-05 05:27
