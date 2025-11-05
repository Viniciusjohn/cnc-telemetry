# 🚀 DIA 6-7: F6 Alertas (Celery + Slack) — Guia de Execução

**Objetivo:** Alertas em tempo real (<5s) com dedupe inteligente  
**Prazo:** 10-11 Nov (2 dias)  
**Status:** 🏃 EM ANDAMENTO

---

## ⚙️ PASSO 1: Instalar Redis (10 min)

```bash
# Instalar Redis
sudo apt update
sudo apt install -y redis-server

# Iniciar serviço
sudo systemctl start redis
sudo systemctl enable redis

# Verificar status
sudo systemctl status redis

# Testar conexão
redis-cli ping
# Esperado: PONG
```

---

## 🐍 PASSO 2: Instalar Dependências Python (5 min)

```bash
cd backend
source .venv/bin/activate

# Instalar Celery + Redis + YAML + HTTP client
pip install celery==5.3.4
pip install redis==5.0.1
pip install pyyaml==6.0.1
pip install httpx==0.25.2

# Atualizar requirements.txt
pip freeze > requirements.txt
```

---

## 🔔 PASSO 3: Configurar Slack Webhook (5 min)

### Criar Webhook no Slack

1. Acessar: https://api.slack.com/messaging/webhooks
2. Criar novo Slack App (ou usar existente)
3. Ativar "Incoming Webhooks"
4. Adicionar webhook a um canal (ex: #cnc-alerts)
5. Copiar Webhook URL: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX`

### Configurar no .env

```bash
# Adicionar ao backend/.env
echo "" >> backend/.env
echo "# Alertas" >> backend/.env
echo "REDIS_URL=redis://localhost:6379/0" >> backend/.env
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" >> backend/.env
```

**⚠️ IMPORTANTE:** Substituir `YOUR/WEBHOOK/URL` pela URL real do Slack!

---

## ⚡ PASSO 4: Configurar Regras de Alertas (5 min)

O arquivo `config/alerts.yaml` já está criado com 4 regras:

```yaml
alerts:
  # Regra 1: Máquina parada >60s
  - name: machine_stopped_long
    condition: "state == 'stopped' AND duration_seconds > 60"
    
  # Regra 2: Execução sem movimento
  - name: execution_no_movement
    condition: "rpm == 0 AND state == 'running'"
    
  # Regra 3: RPM baixo (desabilitada)
  - name: rpm_low_anomaly
    enabled: false
    
  # Regra 4: Feed muito alto (desabilitada)
  - name: feed_too_high
    enabled: false
```

**Opcional:** Editar `config/alerts.yaml` para ajustar:
- Thresholds (ex: `duration_seconds > 120`)
- Habilitar/desabilitar regras (`enabled: true/false`)
- Templates de mensagem
- Webhooks customizados

---

## 🔄 PASSO 5: Testar Alert Engine (10 min)

### Testar Avaliação Manual

```bash
cd backend
source .venv/bin/activate
python3

# No Python REPL:
from app.services.alerts import evaluate_all_alerts, load_alert_rules

# Carregar regras
config = load_alert_rules()
print(f"Regras carregadas: {len(config['alerts'])}")

# Testar avaliação (sem Celery)
result = evaluate_all_alerts()
print(result)
# Esperado: {'alerts_fired': X, 'machines_checked': Y}
```

---

## 🚀 PASSO 6: Rodar Celery Worker (Background)

### Terminal 1: Celery Worker

```bash
cd backend
source .venv/bin/activate

# Rodar worker
celery -A app.services.alerts:celery_app worker \
  --loglevel=info \
  --concurrency=2

# Esperado:
# -------------- celery@hostname v5.3.4 ----------
# --- ***** ----- 
# -- ******* ---- Linux-5.x.x-x86_64 2024-11-10
# - *** --- * --- 
# - ** ---------- [config]
# - ** ---------- .> app:         alerts:0x...
# - ** ---------- .> transport:   redis://localhost:6379/0
# ...
# [tasks]
#   . alerts.evaluate_all
```

**Deixar rodando!** Este terminal deve ficar ativo.

---

## ⏰ PASSO 7: Rodar Celery Beat (Scheduler)

### Terminal 2: Celery Beat

```bash
cd backend
source .venv/bin/activate

# Rodar beat (scheduler)
celery -A app.services.alerts:celery_app beat \
  --loglevel=info

# Esperado:
# celery beat v5.3.4 is starting.
# Scheduler: PersistentScheduler
# ...
# Scheduler: Sending due task evaluate-alerts-every-30s (alerts.evaluate_all)
```

**Deixar rodando!** Este terminal também deve ficar ativo.

---

## 🧪 PASSO 8: Testar Alertas End-to-End (15 min)

### 8.1 Simular Condição de Alerta

```bash
# Terminal 3: Enviar dados simulando máquina parada
curl -X POST http://localhost:8001/v1/telemetry/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "machine_id": "TEST-ALERT-001",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "rpm": 0,
    "feed_mm_min": 0,
    "state": "stopped"
  }'

# Repetir a cada 2 segundos por 70 segundos (para ultrapassar threshold de 60s)
for i in {1..35}; do
  curl -s -X POST http://localhost:8001/v1/telemetry/ingest \
    -H 'Content-Type: application/json' \
    -d '{
      "machine_id": "TEST-ALERT-001",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "rpm": 0,
      "feed_mm_min": 0,
      "state": "stopped"
    }' > /dev/null
  
  echo "Enviado sample $i/35"
  sleep 2
done

echo "✅ Simulação completa. Aguardando alerta no Slack..."
```

### 8.2 Verificar Alerta no Slack

**Esperado (em ~70-90 segundos):**
- Mensagem no canal Slack:
  ```
  🔴 TEST-ALERT-001 parada há 1.2 min (Estado: stopped)
  ```

**Verificar latência:**
- Tempo desde condição atingida (60s parado) até alerta no Slack
- **Target:** < 5 segundos

---

## ✅ PASSO 9: Validar Dedupe (5 min)

```bash
# Aguardar 30 segundos e enviar mais dados (máquina ainda parada)
sleep 30

for i in {1..10}; do
  curl -s -X POST http://localhost:8001/v1/telemetry/ingest \
    -H 'Content-Type: application/json' \
    -d '{
      "machine_id": "TEST-ALERT-001",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "rpm": 0,
      "feed_mm_min": 0,
      "state": "stopped"
    }' > /dev/null
  sleep 2
done

echo "✅ Teste de dedupe completo"
```

**Esperado:**
- ❌ **NÃO** deve enviar novo alerta (dedupe ativo por 60s)
- Verificar logs do Celery worker: "Alert recently fired, skipping..."

---

## 📊 PASSO 10: Validar Métricas de Performance (10 min)

### 10.1 Latência de Alerta

```bash
# Medir tempo desde condição até alerta
# 1. Anotar timestamp quando condição é atingida (60s parado)
START=$(date +%s)

# 2. Aguardar alerta aparecer no Slack
# 3. Anotar timestamp do alerta

# 4. Calcular latência
# Latência = (Timestamp alerta) - (START + 60s)
# Target: < 5s
```

### 10.2 Taxa de Avaliação

```bash
# Verificar logs do Celery beat
# Deve executar a cada 30s:
# [2024-11-10 10:00:00] Scheduler: Sending due task evaluate-alerts-every-30s
# [2024-11-10 10:00:30] Scheduler: Sending due task evaluate-alerts-every-30s
# [2024-11-10 10:01:00] Scheduler: Sending due task evaluate-alerts-every-30s
```

### 10.3 Dedupe Effectiveness

```bash
# Verificar no Redis
redis-cli

# Listar alertas ativos
KEYS alert:*

# Ver TTL de um alerta específico
TTL alert:machine_stopped_long:TEST-ALERT-001
# Esperado: ~55-60 segundos (decrementa)

# Ver valor
GET alert:machine_stopped_long:TEST-ALERT-001
# Esperado: "1"
```

---

## 🎯 Critérios de Aceite F6

- [ ] Redis instalado e rodando
- [ ] Celery worker rodando (2 workers)
- [ ] Celery beat rodando (scheduler 30s)
- [ ] 2 regras de alerta ativas (parada >60s, execução sem movimento)
- [ ] Slack webhook configurado
- [ ] Alerta disparado em < 5s após condição atingida
- [ ] Dedupe funciona (máx 1 alerta/min por regra)
- [ ] Zero falsos positivos em 1h de teste
- [ ] Logs do Celery sem erros críticos

---

## 🐛 Troubleshooting

### Erro: "redis.exceptions.ConnectionError"
```bash
# Verificar se Redis está rodando
sudo systemctl status redis

# Reiniciar Redis
sudo systemctl restart redis

# Testar conexão
redis-cli ping
```

### Erro: "ModuleNotFoundError: No module named 'celery'"
```bash
cd backend
source .venv/bin/activate
pip install celery redis pyyaml httpx
```

### Alerta não dispara no Slack
```bash
# Verificar webhook URL no .env
cat backend/.env | grep SLACK_WEBHOOK_URL

# Testar webhook manualmente
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"🧪 Teste manual de webhook"}'

# Verificar logs do Celery worker
# Procurar por: "✅ Slack alert sent" ou "❌ Failed to send Slack alert"
```

### Celery beat não agenda tarefas
```bash
# Verificar arquivo celerybeat-schedule.db
ls -la celerybeat-schedule.db

# Remover e reiniciar
rm celerybeat-schedule.db
celery -A app.services.alerts:celery_app beat --loglevel=info
```

### Alertas duplicados (dedupe não funciona)
```bash
# Verificar Redis está acessível
redis-cli ping

# Ver chaves de alerta
redis-cli KEYS "alert:*"

# Verificar TTL
redis-cli TTL "alert:machine_stopped_long:MACHINE_ID"
```

---

## 📝 Checklist de Execução

- [ ] PASSO 1: Instalar Redis
- [ ] PASSO 2: Instalar deps Python (Celery, Redis, YAML, HTTPX)
- [ ] PASSO 3: Configurar Slack webhook no .env
- [ ] PASSO 4: Revisar regras em config/alerts.yaml
- [ ] PASSO 5: Testar alert engine manualmente
- [ ] PASSO 6: Rodar Celery worker (Terminal 1)
- [ ] PASSO 7: Rodar Celery beat (Terminal 2)
- [ ] PASSO 8: Simular condição e verificar alerta Slack
- [ ] PASSO 9: Validar dedupe (não duplicar alertas)
- [ ] PASSO 10: Medir latência (<5s)

---

## 🚀 Scripts de Inicialização (Produção)

### Systemd Service para Celery Worker

```bash
# Criar /etc/systemd/system/cnc-celery-worker.service
sudo tee /etc/systemd/system/cnc-celery-worker.service > /dev/null <<EOF
[Unit]
Description=CNC Telemetry Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=viniciusjohn
WorkingDirectory=/home/viniciusjohn/iot/backend
Environment="PATH=/home/viniciusjohn/iot/backend/.venv/bin"
ExecStart=/home/viniciusjohn/iot/backend/.venv/bin/celery -A app.services.alerts:celery_app worker --loglevel=info --detach
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable cnc-celery-worker
sudo systemctl start cnc-celery-worker
```

### Systemd Service para Celery Beat

```bash
# Criar /etc/systemd/system/cnc-celery-beat.service
sudo tee /etc/systemd/system/cnc-celery-beat.service > /dev/null <<EOF
[Unit]
Description=CNC Telemetry Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=viniciusjohn
WorkingDirectory=/home/viniciusjohn/iot/backend
Environment="PATH=/home/viniciusjohn/iot/backend/.venv/bin"
ExecStart=/home/viniciusjohn/iot/backend/.venv/bin/celery -A app.services.alerts:celery_app beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable cnc-celery-beat
sudo systemctl start cnc-celery-beat
```

---

## 📊 Monitoramento (Flower - Opcional)

```bash
# Instalar Flower (UI para Celery)
pip install flower

# Rodar Flower
celery -A app.services.alerts:celery_app flower \
  --port=5555

# Acessar: http://localhost:5555
# Dashboard com tasks, workers, monitoring
```

---

**Tempo Estimado Total:** 1-2 horas  
**Próximo:** DIA 8-10 (F8 OEE Dashboard + CSV Export)
