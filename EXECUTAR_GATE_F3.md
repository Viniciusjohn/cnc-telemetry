# ⚡ F3 Gate Único — Executar AGORA

**Tempo:** ~5 minutos (automatizado)  
**Objetivo:** Validar F3 e fechar issue #4

---

## 🚀 Passo 1: Iniciar Serviços (2 terminais)

### Terminal 1 - Simulador
```bash
cd /home/viniciusjohn/iot
python3 scripts/mtconnect_simulator.py --port 5000
```

### Terminal 2 - Backend
```bash
cd /home/viniciusjohn/iot/backend
source .venv/bin/activate
uvicorn app:app --port 8001 --reload
```

**Aguardar:** Backend inicializar (~5s)

---

## 🧪 Passo 2: Executar Gate Automatizado

### Terminal 3 - Gate
```bash
cd /home/viniciusjohn/iot
./scripts/gate_f3.sh
```

**Saída esperada:**
```
═══════════════════════════════════════════════════════════
  F3 — GATE ÚNICO DE VALIDAÇÃO
═══════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate 1/7: Headers Canônicos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Cache-Control: no-store
  ✓ Vary
  ✓ X-Contract-Fingerprint
  ✓ Server-Timing
✅ PASS - Gate 1: Headers canônicos (4/4)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gate 2/7: Schema JSON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ rpm válido: 4200.5
  ✓ feed_mm_min válido: 870.0
  ✓ state válido: running
  ✓ updated_at presente: 2025-11-05T06:40:00Z
✅ PASS - Gate 2: Schema JSON válido

...

═══════════════════════════════════════════════════════════
  ✅ PASS: 5  |  ❌ FAIL: 0  (Gates 1-5)
═══════════════════════════════════════════════════════════

🎉 Gates 1-5 passaram!

Próximos passos:
  1. Validar UI (Gate 6): http://localhost:5173
  2. Executar Playwright (Gate 7): cd frontend && npx playwright test
  3. Preencher campos manuais em docs/F3_GATE_UNICO_*.md
  4. Anexar relatório na issue #4

📝 Relatório salvo em: docs/F3_GATE_UNICO_20251105_064000.md
```

---

## 🖥️ Passo 3: Validar UI (Manual)

### Terminal 4 - Frontend
```bash
cd /home/viniciusjohn/iot/frontend
npm run dev
```

### Abrir Navegador
```
http://localhost:5173
```

### Checklist (Marcar no Relatório)

- [ ] Header "CNC Telemetry — Dashboard" visível
- [ ] Machine ID "CNC-SIM-001" no topo direito
- [ ] 4 cards: RPM, Feed, Estado, Atualizado
- [ ] Valores atualizam a cada ~2s (observar timestamp)
- [ ] Cores corretas:
  - 🟢 Verde = RODANDO
  - 🔴 Vermelho = PARADA
  - 🟡 Amarelo = OCIOSA
- [ ] Console sem erros (F12 → Console)

### Capturar Screenshots

**Desktop:**
- Print Screen ou ferramenta de captura

**Mobile (Simular):**
1. F12 → Toggle Device Toolbar (Ctrl+Shift+M)
2. Selecionar "iPhone 12 Pro"
3. Print Screen

**Salvar em:** `docs/screenshots/f3_desktop.png`, `docs/screenshots/f3_mobile.png`

---

## 🎭 Passo 4: Executar Playwright

### Terminal 5
```bash
cd /home/viniciusjohn/iot/frontend
npx playwright test e2e/status.spec.ts --reporter=list
```

**Saída esperada:**
```
✓ Dashboard F3 › deve exibir header e machine_id (2s)
✓ Dashboard F3 › deve exibir 4 cards de status (1s)
✓ Dashboard F3 › cards devem atualizar após 2s (polling) (3s)
✓ Dashboard F3 › deve exibir erro se backend não disponível (1s)

4 passed (7s)
```

**Copiar saída** para o relatório.

---

## 📝 Passo 5: Preencher Relatório

### Abrir Relatório Gerado

```bash
# Localizar arquivo
ls -lt docs/F3_GATE_UNICO_*.md | head -1

# Abrir (exemplo)
nano docs/F3_GATE_UNICO_20251105_064000.md
```

### Preencher Seções Manuais

1. **Gate 6 (UI Dashboard):**
   - Marcar checklist
   - Anexar screenshots
   - Marcar resultado (✅ PASS / ❌ FAIL)

2. **Gate 7 (Playwright):**
   - Colar output do npx playwright test
   - Marcar resultado (✅ PASS / ❌ FAIL)

3. **Veredito Final:**
   - Atualizar tabela com status dos 7 gates
   - Se 7/7 PASS: **Status: ✅ PASS**
   - Se algum FAIL: **Status: ❌ FAIL** (corrigir e re-executar)

---

## 📎 Passo 6: Anexar na Issue #4

### Commit Screenshots (se houver)

```bash
cd /home/viniciusjohn/iot
git add docs/screenshots/
git add docs/F3_GATE_UNICO_*.md
git commit -m "F3 Gate: Validação completa - 7/7 PASS"
git push origin main
```

### Anexar na Issue

**Opção 1 - Via gh CLI:**
```bash
REPORT=$(ls -t docs/F3_GATE_UNICO_*.md | head -1)
gh issue comment 4 -R Viniciusjohn/cnc-telemetry --body-file "$REPORT"
```

**Opção 2 - Manual:**
1. Abrir https://github.com/Viniciusjohn/cnc-telemetry/issues/4
2. Copiar conteúdo do relatório
3. Colar como comentário
4. Anexar screenshots (arrastar arquivos)

---

## ✅ Critério de Aceite F3

**PASS se:**
- ✅ Gates 1-5: 5/5 automatizados PASS
- ✅ Gate 6: UI funcional, checklist completo
- ✅ Gate 7: Playwright 4/4 PASS

**Total: 7/7 PASS**

---

## 🎯 Próximos Passos (Após F3 PASS)

### 1. Fechar Issue #4

```bash
gh issue close 4 -R Viniciusjohn/cnc-telemetry \
  -c "F3 PASS: 7/7 gates validados. Dashboard PWA funcional com polling 2s, headers canônicos e MTConnect compliance."
```

---

### 2. Enviar Email para Nestor (F4 Campo)

```bash
cat docs/email_novatech.md
# Revisar e enviar
```

**Solicitar:**
- Série da máquina (M70/M700/M80/M800)
- IP do MTConnect Agent: `192.168.1.___`
- Porta (geralmente 5000)
- Janela de 2h para testes

---

### 3. Aguardar Confirmação

- [ ] Nestor responde com série/IP
- [ ] Janela agendada
- [ ] Preparar equipamentos para campo
- [ ] Executar F4 conforme `docs/F4_PLANEJAMENTO.md`

---

## 🚨 Troubleshooting

### Gate 1-5 Falha

**Backend não responde:**
```bash
# Verificar porta
lsof -i :8001

# Reiniciar
cd backend && source .venv/bin/activate
uvicorn app:app --port 8001 --reload
```

**Agent não responde:**
```bash
# Verificar porta
lsof -i :5000

# Reiniciar
python3 scripts/mtconnect_simulator.py --port 5000
```

---

### Gate 6 (UI) Falha

**Frontend não compila:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**VITE_API_BASE incorreto:**
```bash
# Verificar
grep -r "VITE_API_BASE" frontend/src/

# Deve usar: import.meta.env.VITE_API_BASE
```

---

### Gate 7 (Playwright) Falha

**Playwright não instalado:**
```bash
cd frontend
npx playwright install
npx playwright install-deps
```

**Backend não acessível durante teste:**
```bash
# Garantir backend rodando antes de executar
curl -s http://localhost:8001/v1/machines/CNC-SIM-001/status
```

---

## 📊 Resumo dos 3 Pontos Críticos MTConnect

### 1. PathFeedrate: mm/s → mm/min (×60)

**XML (Agent):**
```xml
<PathFeedrate units="MILLIMETER/SECOND">14.5</PathFeedrate>
```

**API (Backend):**
```json
{
  "feed_mm_min": 870.0  // 14.5 × 60
}
```

---

### 2. RotaryVelocity (NÃO SpindleSpeed)

**Preferir:**
```xml
<RotaryVelocity units="REVOLUTION/MINUTE">4200</RotaryVelocity>
```

**Evitar (legado):**
```xml
<SpindleSpeed>4200</SpindleSpeed>  <!-- deprecated -->
```

---

### 3. /sample com nextSequence

**Header MTConnect:**
```xml
<Header instanceId="123" nextSequence="12345" .../>
```

**Próximo request:**
```bash
curl "http://localhost:5000/sample?from=12345&count=200"
```

**Resultado:** Continuidade sem gaps

---

## 📚 Referências

- **F2 PASS:** https://github.com/Viniciusjohn/cnc-telemetry/issues/3
- **F3 Planejamento:** `docs/F3_PLANEJAMENTO.md`
- **F4 Planejamento:** `docs/F4_PLANEJAMENTO.md`
- **MTConnect Compliance:** `docs/MTConnect_COMPLIANCE.md`
- **Repositório:** https://github.com/Viniciusjohn/cnc-telemetry

---

**⚡ Tempo total: ~5 minutos**

**🎯 Ao concluir, F3 estará PASS e pronto para F4 (campo)!**
