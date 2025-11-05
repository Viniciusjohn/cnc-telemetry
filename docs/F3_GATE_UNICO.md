# F3 — Gate Único de Validação

**Data de Execução:** ___/___/2025  
**Executor:** _______________________

---

## ✅ Resultado dos Gates

| Gate | Status | Observação |
|------|--------|------------|
| 1. Headers canônicos | ⏳ | |
| 2. Schema JSON | ⏳ | |
| 3. Preflight 204 | ⏳ | |
| 4. MTConnect /current | ⏳ | |
| 5. MTConnect /sample | ⏳ | |
| 6. UI Dashboard | ⏳ | |
| 7. Playwright E2E | ⏳ | |

---

## 📋 Gate 1: Headers Canônicos

**Comando:**
```bash
curl -sI http://localhost:8001/v1/machines/CNC-SIM-001/status | \
  grep -Ei 'cache-control|vary|server-timing|x-contract-fingerprint'
```

**Output:**
```
[Colar aqui]
```

**Resultado:** ✅ PASS / ❌ FAIL

---

## 📋 Gate 2: Schema JSON

**Comando:**
```bash
curl -s http://localhost:8001/v1/machines/CNC-SIM-001/status | \
  jq -e '.rpm>=0 and .feed_mm_min>=0 and (.state | IN("running","stopped","idle"))'
```

**Output:**
```
[Colar aqui]
```

**Dados completos:**
```json
[Colar curl -s ... | jq aqui]
```

**Resultado:** ✅ PASS / ❌ FAIL

---

## 📋 Gate 3: Preflight 204

**Comando:**
```bash
curl -s -X OPTIONS http://localhost:8001/v1/machines/CNC-SIM-001/status \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -D - | head -20
```

**Output:**
```
[Colar aqui]
```

**Verificações:**
- [ ] Status 204 No Content
- [ ] Content-Length: 0 (ou ausente)
- [ ] CORS headers presentes

**Resultado:** ✅ PASS / ❌ FAIL

---

## 📋 Gate 4: MTConnect /current

**Comando:**
```bash
AGENT=http://localhost:5000
curl -s $AGENT/current | xmllint --format - | \
  grep -E "RotaryVelocity|PathFeedrate|Execution|units"
```

**Output:**
```xml
[Colar aqui]
```

**Verificações:**
- [ ] RotaryVelocity presente (não SpindleSpeed)
- [ ] PathFeedrate units="MILLIMETER/SECOND"
- [ ] Execution canônico (ACTIVE/STOPPED/READY)

**Conversão validada:**
- PathFeedrate XML: _____ mm/s
- PathFeedrate API: _____ mm/min
- Conversão correta (×60): ✅ / ❌

**Resultado:** ✅ PASS / ❌ FAIL

---

## 📋 Gate 5: MTConnect /sample

**Comando:**
```bash
curl -s "http://localhost:5000/sample?count=5" | xmllint --format - | \
  grep -E "Header|nextSequence|sequence="
```

**Output:**
```xml
[Colar aqui]
```

**Verificações:**
- [ ] nextSequence presente no Header
- [ ] sequence crescente nas amostras
- [ ] Sem gaps (monotônico)

**Resultado:** ✅ PASS / ❌ FAIL

---

## 📋 Gate 6: UI Dashboard

**URL:** http://localhost:5173

### Checklist Visual

- [ ] Header "CNC Telemetry — Dashboard" visível
- [ ] Machine ID "CNC-SIM-001" no topo direito
- [ ] 4 cards presentes (RPM, Feed, Estado, Atualizado)
- [ ] Valores atualizam a cada ~2s
- [ ] Cores corretas por estado:
  - [ ] 🟢 Verde (RODANDO)
  - [ ] 🔴 Vermelho (PARADA)
  - [ ] 🟡 Amarelo (OCIOSA)
- [ ] Console sem erros
- [ ] Footer mostra "Polling: 2s"

### Screenshots

**Desktop:**
```
[Anexar screenshot]
```

**Mobile (F12 → Device Toolbar):**
```
[Anexar screenshot]
```

**Resultado:** ✅ PASS / ❌ FAIL

---

## 📋 Gate 7: Playwright E2E

**Comando:**
```bash
cd frontend
npx playwright test e2e/status.spec.ts --reporter=list
```

**Output:**
```
[Colar aqui]
```

**Verificações:**
- [ ] Teste 1: Header e machine_id
- [ ] Teste 2: 4 cards de status
- [ ] Teste 3: Polling funcional
- [ ] Teste 4: Erro se backend offline

**Resultado:** ✅ PASS (4/4) / ❌ FAIL

---

## 🎯 Veredito Final

**Total:** ___/7 gates PASS

**Status F3:**
- ✅ **PASS** — Se 7/7 gates passarem
- ❌ **FAIL** — Se algum gate falhar

**Próximo Passo:**
- Se PASS: Anexar este relatório na issue #4 e avançar para F4 (campo)
- Se FAIL: Corrigir issues e re-executar gates que falharam

---

## 📝 Observações

[Notas adicionais, problemas encontrados, etc.]

---

**Assinado:**

**Nome:** _______________________  
**Data:** ___/___/2025  
**Hora:** ___:___
