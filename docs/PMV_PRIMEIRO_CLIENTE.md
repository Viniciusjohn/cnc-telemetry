# 🎯 PMV para Fechar 1º Cliente

**Objetivo:** Fechar o primeiro cliente pagante com prova de ROI  
**Timeline:** 1 sprint (7-10 dias)  
**Investimento:** R$ 99/máquina/mês  
**PoC:** 2h em campo

---

## 💼 Checklist Mínimo para Vender (One-Pager Técnico)

### Técnico
- [x] ✅ Adapter MTConnect estável (sequência OK) — F2 PASS
- [x] ✅ Dashboard real-time (no-store/Vary) — F3 PASS
- [ ] 🔜 Histórico 30 dias + queries rápidas — F5 (7d)
- [ ] 🔜 OEE (A×P×Q) diário com gráfico — F8 (14d)
- [ ] 🔜 2 alertas prontos (parada >60s, anomalia) — F6 (7d)
- [ ] 🔜 Script PoC 2h + relatório padrão
- [ ] 🔜 Proposta comercial simples

### Comercial
- [ ] Pricing: R$ 99/máquina/mês
- [ ] Contrato 1-pager (mensal, cancelável)
- [ ] SLA básico (99% uptime)

### Diferencial
- [ ] ♻️ Plano "pronto-para" OPC-UA
- [ ] ♻️ Plano buffer/QoS 1 para campo

---

## 🎯 Gates de Validação

### G1: Telemetria MTConnect ✅ PASS
```bash
curl -s http://localhost:5000/sample?count=5 | xmllint --format - | grep sequence
# Esperado: nextSequence crescente
```

### G2: API Status Headers ✅ PASS
```bash
curl -sI http://localhost:8001/v1/machines/CNC-SIM-001/status | grep -i cache-control
# Esperado: cache-control: no-store
```

### G3: Histórico 30d 🔜 7 dias
```sql
EXPLAIN ANALYZE 
SELECT time_bucket('5 min', ts), avg(rpm)
FROM telemetry WHERE machine_id='ABR-850' 
AND ts > NOW() - INTERVAL '30 days'
GROUP BY 1;
-- Target: < 2s
```

### G4: OEE Básico 🔜 14 dias
```bash
curl "http://localhost:8001/v1/machines/ABR-850/oee?date=2025-11-05" | jq '.daily_avg'
# Esperado: 0.0-1.0
```

### G5: Alertas 🔜 7 dias
```bash
# Simular parada >60s
curl -X POST http://localhost:8001/v1/telemetry/ingest \
  -d '{"machine_id":"TEST","rpm":0,"state":"stopped"}'
sleep 65
# Verificar Slack: < 5s latência
```

### G6: PoC Campo 🔜 Após G3-G5
```bash
python3 backend/mtconnect_adapter.py \
  --agent-url http://10.0.1.50:5000 \
  --machine-id ABR-850
# Monitorar 2h, gerar relatório
```

---

## 🚧 Riscos e Mitigações

### 1. OEE Impreciso
**Mitigação:** Validar sequências sem gaps
```sql
SELECT sequence, LAG(sequence) OVER (ORDER BY ts) AS prev, 
  sequence - LAG(sequence) OVER (ORDER BY ts) AS gap
FROM telemetry WHERE gap > 1;
-- Esperado: sem resultados
```

### 2. Cache Status
**Mitigação:** `Cache-Control: no-store` em TODAS respostas `/status`
[Ref: MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)

### 3. Cliente Exige OPC-UA
**Mitigação:** Pitch roadmap Q1'26 + desconto 20% early bird
[Ref: OPC-UA](https://documentation.unified-automation.com/)

### 4. Rede Instável
**Mitigação:** Buffer local (Q2'26), aceitar < 0.5% perda no PMV
[Ref: MQTT QoS](https://docs.oasis-open.org/mqtt/mqtt/v5.0/)

---

## 📋 Próximo Passo (1 Sprint)

### Dia 1-2: F3 Gate
- [ ] Playwright smoke tests
- [ ] Screenshots

### Dia 3-5: F5 TimescaleDB
- [ ] Install PostgreSQL + TimescaleDB
- [ ] Schema + hypertable
- [ ] Retention 30d
- [ ] Aggregates (5m, 1h, 1d)
- [ ] `/history` endpoint

### Dia 6-7: F6 Alertas
- [ ] Celery + Redis
- [ ] 2 regras (parada >60s, anomalia)
- [ ] Slack integration

### Dia 8-10: F8 OEE
- [ ] Schema `oee_daily`
- [ ] `calculate_oee()`
- [ ] `/oee` endpoint
- [ ] Dashboard card + CSV export

### Dia 11: PoC Package
- [ ] Template relatório
- [ ] Proposta comercial
- [ ] Contrato

---

**Versão:** 1.0  
**Data:** 2025-11-05
