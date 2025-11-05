# 🚀 DIA 8-10: F8 OEE Dashboard + CSV Export — Guia de Execução

**Objetivo:** Dashboard OEE com gráficos e export CSV  
**Prazo:** 12-14 Nov (3 dias)  
**Status:** 🏃 EM ANDAMENTO

---

## 📦 PASSO 1: Instalar Dependências Frontend (5 min)

```bash
cd frontend

# Instalar Chart.js e React wrapper
npm install chart.js react-chartjs-2

# Verificar instalação
npm list chart.js react-chartjs-2
```

**Esperado:**
```
chart.js@4.4.0
react-chartjs-2@5.2.0
```

---

## 🔧 PASSO 2: Wire OEE Router no Backend (2 min)

O arquivo `backend/main.py` já foi atualizado com:
- ✅ Import de `oee` router
- ✅ `app.include_router(oee.router)`
- ✅ `/ingest` agora grava no TimescaleDB

**Verificar:**
```bash
cd backend
grep "oee" main.py
# Esperado: from app.routers import status, history, oee
#           app.include_router(oee.router)
```

---

## 🎨 PASSO 3: Adicionar OEE Card ao Dashboard (10 min)

### 3.1 Importar Componente

Editar `frontend/src/App.tsx`:

```typescript
// No início do arquivo, adicionar import
import { OEECard } from './components/OEECard';

// Dentro do return, após os cards de status, adicionar:
<OEECard machineId={machineId} />
```

**Exemplo completo:**
```typescript
return (
  <div className="min-h-screen bg-gray-100 p-8">
    <h1 className="text-3xl font-bold text-gray-900 mb-8">
      CNC Telemetry Dashboard
    </h1>

    {/* Cards de Status Existentes */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* RPM Card */}
      {/* Feed Card */}
      {/* State Card */}
    </div>

    {/* Novo: OEE Card */}
    <div className="mb-8">
      <OEECard machineId={machineId} />
    </div>

    {error && (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    )}
  </div>
);
```

---

## 🚀 PASSO 4: Rodar Backend com OEE (5 min)

```bash
cd backend
source .venv/bin/activate

# Verificar database está rodando
psql -U cnc_user -d cnc_telemetry -c "SELECT COUNT(*) FROM telemetry;"

# Rodar backend
uvicorn main:app --port 8001 --reload

# Em outro terminal, verificar endpoints OEE
curl http://localhost:8001/docs
# Acessar Swagger UI e verificar:
# - GET /v1/machines/{machine_id}/oee
# - GET /v1/machines/{machine_id}/oee/trend
# - GET /v1/machines/{machine_id}/oee/export
```

---

## 🎨 PASSO 5: Rodar Frontend com OEE Card (5 min)

```bash
cd frontend

# Rodar dev server
npm run dev

# Acessar: http://localhost:5173
```

**Esperado:**
- Card "OEE (Overall Equipment Effectiveness)" visível
- Valor de OEE hoje (ex: 68.4%)
- Badge com classificação (Poor/Fair/Good/World-Class)
- 3 métricas: Availability, Performance, Quality
- Gráfico de 7 dias (linha)
- Botão "Download CSV"

---

## 📊 PASSO 6: Popular Dados de Teste (10 min)

Para testar OEE, precisamos de dados históricos:

```bash
# Script para popular dados de teste (30 dias)
cat > backend/populate_test_data.py << 'EOF'
import psycopg2
from datetime import datetime, timedelta
import random

# Connect to database
conn = psycopg2.connect(
    "postgresql://cnc_user:cnc_telemetry_2025@localhost/cnc_telemetry"
)
cur = conn.cursor()

# Generate 30 days of data (2-second intervals, 8 hours/day)
machine_id = "CNC-SIM-001"
now = datetime.now()

print("Populating test data...")

for day in range(30):
    date = now - timedelta(days=day)
    
    # 8 hours of operation per day (06:00-14:00)
    for hour in range(6, 14):
        for minute in range(0, 60, 1):  # Every minute for speed
            ts = datetime(date.year, date.month, date.day, hour, minute, 0)
            
            # Simulate realistic states
            # 70% running, 20% idle, 10% stopped
            rand = random.random()
            if rand < 0.70:
                state = 'running'
                rpm = random.randint(4000, 5000)
                feed = random.randint(1000, 1500)
            elif rand < 0.90:
                state = 'idle'
                rpm = 0
                feed = 0
            else:
                state = 'stopped'
                rpm = 0
                feed = 0
            
            try:
                cur.execute("""
                    INSERT INTO telemetry (ts, machine_id, rpm, feed_mm_min, state)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (ts, machine_id, rpm, feed, state))
            except Exception as e:
                print(f"Error inserting: {e}")
    
    conn.commit()
    print(f"Day {30-day}/30 complete")

print("✅ Test data populated!")
print(f"Total samples: {30 * 8 * 60}")

cur.close()
conn.close()
EOF

# Rodar script
python3 backend/populate_test_data.py

# Verificar dados
psql -U cnc_user -d cnc_telemetry -c "
SELECT 
  DATE(ts) AS date,
  COUNT(*) AS samples,
  SUM(CASE WHEN state='running' THEN 1 ELSE 0 END) AS running,
  SUM(CASE WHEN state='stopped' THEN 1 ELSE 0 END) AS stopped,
  SUM(CASE WHEN state='idle' THEN 1 ELSE 0 END) AS idle
FROM telemetry 
WHERE machine_id='CNC-SIM-001'
GROUP BY DATE(ts)
ORDER BY date DESC
LIMIT 7;
"
```

---

## 🧪 PASSO 7: Testar Cálculo OEE (10 min)

### 7.1 Testar API Manualmente

```bash
# OEE de hoje
TODAY=$(date +%Y-%m-%d)
curl "http://localhost:8001/v1/machines/CNC-SIM-001/oee?date=$TODAY&shift=daily" | jq

# Esperado:
# {
#   "date": "2025-11-05",
#   "machine_id": "CNC-SIM-001",
#   "shift": "daily",
#   "oee": 0.6845,  # 68.45%
#   "availability": 0.7234,
#   "performance": 0.9456,
#   "quality": 1.0,
#   "benchmark": {
#     "label": "⚠️ Razoável",
#     "color": "#f59e0b",
#     "classification": "fair"
#   }
# }
```

### 7.2 Testar Trend (7 dias)

```bash
FROM_DATE=$(date -d '7 days ago' +%Y-%m-%d)
TO_DATE=$(date +%Y-%m-%d)

curl "http://localhost:8001/v1/machines/CNC-SIM-001/oee/trend?from_date=$FROM_DATE&to_date=$TO_DATE&shift=daily" | jq '.trend | length'

# Esperado: 8 (7 dias + hoje)
```

### 7.3 Testar Export CSV

```bash
FROM_DATE=$(date -d '30 days ago' +%Y-%m-%d)
TO_DATE=$(date +%Y-%m-%d)

curl "http://localhost:8001/v1/machines/CNC-SIM-001/oee/export?format=csv&from_date=$FROM_DATE&to_date=$TO_DATE" -o oee_export.csv

# Verificar arquivo
head -10 oee_export.csv

# Esperado:
# date,machine_id,shift,planned_time_min,operating_time_min,availability,performance,quality,oee
# 2025-10-06,CNC-SIM-001,daily,1440.0,1041.6,0.7233,0.9456,1.0,0.6841
# 2025-10-07,CNC-SIM-001,daily,1440.0,1038.2,0.7210,0.9472,1.0,0.6828
# ...
```

---

## ✅ PASSO 8: Validar Dashboard OEE (10 min)

### 8.1 Verificar Card OEE

Abrir http://localhost:5173

**Checklist Visual:**
- [ ] Card "OEE" visível
- [ ] Valor grande (ex: 68.4%) com cor apropriada
- [ ] Badge de classificação (Poor/Fair/Good/World-Class)
- [ ] 3 métricas (Availability, Performance, Quality)
- [ ] Gráfico de 7 dias renderizado corretamente
- [ ] Linha OEE (azul) e Availability (verde tracejada)
- [ ] Eixo Y vai de 0-100%
- [ ] Labels de data no eixo X
- [ ] Botão "Download CSV" visível

### 8.2 Testar Download CSV

- Clicar em "Download CSV"
- Arquivo `oee_CNC-SIM-001_YYYY-MM-DD_YYYY-MM-DD.csv` deve baixar
- Abrir no Excel/LibreOffice
- Verificar dados formatados corretamente

### 8.3 Testar Responsividade

```bash
# Abrir DevTools (F12)
# Testar viewports:
# - Desktop (1920x1080)
# - Tablet (768x1024)
# - Mobile (375x667)

# Card OEE deve adaptar:
# - Gráfico deve manter aspect ratio
# - Métricas devem empilhar em mobile
# - Botão CSV deve permanecer visível
```

---

## 📊 PASSO 9: Validar Cálculo OEE (15 min)

### 9.1 Calcular Manualmente

```sql
-- Calcular OEE manualmente para hoje
psql -U cnc_user -d cnc_telemetry

SELECT 
  DATE(ts) AS date,
  COUNT(*) AS total_samples,
  SUM(CASE WHEN state='running' THEN 1 ELSE 0 END) AS running_samples,
  SUM(CASE WHEN state='running' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS availability,
  AVG(CASE WHEN state='running' THEN rpm ELSE NULL END) AS avg_rpm
FROM telemetry
WHERE machine_id = 'CNC-SIM-001'
  AND DATE(ts) = CURRENT_DATE
GROUP BY DATE(ts);

-- Calcular OEE:
-- Availability = running_samples / total_samples
-- Performance = avg_rpm / 4500 (programmed RPM)
-- Quality = 1.0 (assumido)
-- OEE = Availability × Performance × Quality
```

### 9.2 Comparar com API

```bash
curl "http://localhost:8001/v1/machines/CNC-SIM-001/oee?date=$(date +%Y-%m-%d)&shift=daily" | jq '{availability, performance, quality, oee}'

# Comparar valores com cálculo manual
# Diferença deve ser < 1%
```

---

## 🎯 PASSO 10: Benchmarks e Metas (5 min)

### 10.1 Verificar Classificação

```bash
# Verificar benchmark para diferentes OEEs
for oee in 0.55 0.65 0.75 0.90; do
  echo "OEE: $oee"
  # API retorna classificação automaticamente
done
```

**Classificações Esperadas:**
- < 60%: ❌ Inaceitável (Poor)
- 60-70%: ⚠️ Razoável (Fair)
- 70-85%: ✅ Competitivo (Good)
- > 85%: 🏆 World Class

### 10.2 Definir Metas

Criar arquivo `config/oee_targets.yaml`:

```yaml
targets:
  poor: 0.60
  fair: 0.70
  good: 0.85
  world_class: 0.90

alerts:
  - condition: "oee < 0.60"
    severity: critical
    message: "OEE crítico: {oee}% (Meta: >60%)"
  
  - condition: "oee < 0.70"
    severity: warning
    message: "OEE baixo: {oee}% (Meta: >70%)"
```

---

## 📈 PASSO 11: Capturar Screenshots OEE (5 min)

```bash
# Adicionar ao scripts/capture_screenshots.ts
# Capturar dashboard com OEE card visível

# Ou manualmente:
# 1. Abrir http://localhost:5173
# 2. F12 DevTools → Screenshots
# 3. Capturar desktop (1920x1080)
# 4. Capturar mobile (375x667)
# 5. Salvar em docs/screenshots/
#    - dashboard-oee-desktop.png
#    - dashboard-oee-mobile.png
```

---

## ✅ Critérios de Aceite F8

- [ ] Chart.js instalado no frontend
- [ ] OEE Card renderiza sem erros
- [ ] Cálculo OEE correto (A×P×Q)
- [ ] Gráfico 7 dias funcional
- [ ] Download CSV funciona
- [ ] Responsivo (desktop/tablet/mobile)
- [ ] Benchmarks corretos (Poor/Fair/Good/World-Class)
- [ ] Dados de teste populados (30 dias)
- [ ] Backend routers wired corretamente
- [ ] Screenshots capturados

---

## 🐛 Troubleshooting

### Erro: "Cannot find module 'chart.js'"
```bash
cd frontend
npm install chart.js react-chartjs-2
```

### OEE sempre 0% ou NaN
```bash
# Verificar dados no banco
psql -U cnc_user -d cnc_telemetry -c "SELECT COUNT(*) FROM telemetry WHERE machine_id='CNC-SIM-001';"

# Se 0, popular dados de teste
python3 backend/populate_test_data.py
```

### Gráfico não renderiza
```bash
# Verificar console do browser (F12)
# Erro comum: "Chart.js not registered"

# Solução: Verificar imports em OEECard.tsx
# ChartJS.register(...) deve estar presente
```

### CSV download não funciona
```bash
# Verificar CORS headers no backend
# main.py deve ter:
# allow_methods=["GET","POST","OPTIONS"]

# Testar endpoint diretamente
curl -I "http://localhost:8001/v1/machines/CNC-SIM-001/oee/export?format=csv"
# Deve retornar Content-Type: text/csv
```

### Performance ruim (gráfico lento)
```bash
# Reduzir número de pontos
# Em OEECard.tsx, limitar trend a 7 dias

# Ou usar aggregates
curl ".../oee/trend?resolution=1d"
```

---

## 📝 Checklist de Execução

- [ ] PASSO 1: Instalar Chart.js
- [ ] PASSO 2: Wire OEE router
- [ ] PASSO 3: Adicionar OEE Card ao App.tsx
- [ ] PASSO 4: Rodar backend
- [ ] PASSO 5: Rodar frontend
- [ ] PASSO 6: Popular dados de teste
- [ ] PASSO 7: Testar cálculo OEE
- [ ] PASSO 8: Validar dashboard visual
- [ ] PASSO 9: Validar cálculo manual vs API
- [ ] PASSO 10: Verificar benchmarks
- [ ] PASSO 11: Capturar screenshots

---

**Tempo Estimado Total:** 2-3 horas  
**Próximo:** DIA 11 (PoC Package Final)
