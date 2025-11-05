#!/usr/bin/env bash
# Gate Único F3 — Validação Completa Automatizada
# Executa 7 gates e gera relatório

set -euo pipefail

API_URL="${API_URL:-http://localhost:8001}"
AGENT_URL="${AGENT_URL:-http://localhost:5000}"
MACHINE_ID="${MACHINE_ID:-CNC-SIM-001}"
REPORT_FILE="docs/F3_GATE_UNICO_$(date +%Y%m%d_%H%M%S).md"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  F3 — GATE ÚNICO DE VALIDAÇÃO"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "API: $API_URL"
echo "Agent: $AGENT_URL"
echo "Machine: $MACHINE_ID"
echo "Relatório: $REPORT_FILE"
echo ""

PASS=0
FAIL=0

function gate_pass() {
    echo -e "${GREEN}✅ PASS${NC} - Gate $1: $2"
    ((PASS++))
}

function gate_fail() {
    echo -e "${RED}❌ FAIL${NC} - Gate $1: $2"
    ((FAIL++))
}

function section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Inicializar relatório
cat > "$REPORT_FILE" <<EOF
# F3 — Gate Único de Validação (Executado Automaticamente)

**Data:** $(date '+%Y-%m-%d %H:%M:%S')  
**API:** $API_URL  
**Agent:** $AGENT_URL  
**Machine ID:** $MACHINE_ID

---

## ✅ Resultado Resumido

EOF

# ═══════════════════════════════════════════════════════════
# GATE 1: Headers Canônicos
# ═══════════════════════════════════════════════════════════
section "Gate 1/7: Headers Canônicos"

echo "Comando: curl -sI $API_URL/v1/machines/$MACHINE_ID/status"
echo ""

HEADERS=$(curl -sI "$API_URL/v1/machines/$MACHINE_ID/status" 2>/dev/null || echo "")

cat >> "$REPORT_FILE" <<EOF
### Gate 1: Headers Canônicos

\`\`\`bash
curl -sI $API_URL/v1/machines/$MACHINE_ID/status | \\
  grep -Ei 'cache-control|vary|server-timing|x-contract-fingerprint'
\`\`\`

**Output:**
\`\`\`
$HEADERS
\`\`\`

EOF

GATE1_OK=true
if echo "$HEADERS" | grep -qi "cache-control: no-store"; then
    echo "  ✓ Cache-Control: no-store"
else
    echo "  ✗ Cache-Control: no-store AUSENTE"
    GATE1_OK=false
fi

if echo "$HEADERS" | grep -qi "vary:"; then
    echo "  ✓ Vary"
else
    echo "  ✗ Vary AUSENTE"
    GATE1_OK=false
fi

if echo "$HEADERS" | grep -qi "x-contract-fingerprint:"; then
    echo "  ✓ X-Contract-Fingerprint"
else
    echo "  ✗ X-Contract-Fingerprint AUSENTE"
    GATE1_OK=false
fi

if echo "$HEADERS" | grep -qi "server-timing:"; then
    echo "  ✓ Server-Timing"
else
    echo "  ✗ Server-Timing AUSENTE"
    GATE1_OK=false
fi

if $GATE1_OK; then
    gate_pass "1" "Headers canônicos (4/4)"
    echo "**Resultado:** ✅ PASS" >> "$REPORT_FILE"
else
    gate_fail "1" "Headers incompletos"
    echo "**Resultado:** ❌ FAIL" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ═══════════════════════════════════════════════════════════
# GATE 2: Schema JSON
# ═══════════════════════════════════════════════════════════
section "Gate 2/7: Schema JSON"

echo "Comando: curl -s $API_URL/v1/machines/$MACHINE_ID/status | jq"
echo ""

JSON=$(curl -s "$API_URL/v1/machines/$MACHINE_ID/status" 2>/dev/null || echo "{}")

cat >> "$REPORT_FILE" <<EOF
### Gate 2: Schema JSON

\`\`\`bash
curl -s $API_URL/v1/machines/$MACHINE_ID/status | jq
\`\`\`

**Output:**
\`\`\`json
$JSON
\`\`\`

EOF

GATE2_OK=true
if echo "$JSON" | jq -e '.rpm >= 0' >/dev/null 2>&1; then
    RPM=$(echo "$JSON" | jq -r '.rpm')
    echo "  ✓ rpm válido: $RPM"
else
    echo "  ✗ rpm inválido ou ausente"
    GATE2_OK=false
fi

if echo "$JSON" | jq -e '.feed_mm_min >= 0' >/dev/null 2>&1; then
    FEED=$(echo "$JSON" | jq -r '.feed_mm_min')
    echo "  ✓ feed_mm_min válido: $FEED"
else
    echo "  ✗ feed_mm_min inválido ou ausente"
    GATE2_OK=false
fi

if echo "$JSON" | jq -e '.state | IN("running","stopped","idle")' >/dev/null 2>&1; then
    STATE=$(echo "$JSON" | jq -r '.state')
    echo "  ✓ state válido: $STATE"
else
    echo "  ✗ state inválido"
    GATE2_OK=false
fi

if echo "$JSON" | jq -e '.updated_at' >/dev/null 2>&1; then
    UPDATED=$(echo "$JSON" | jq -r '.updated_at')
    echo "  ✓ updated_at presente: $UPDATED"
else
    echo "  ✗ updated_at ausente"
    GATE2_OK=false
fi

if $GATE2_OK; then
    gate_pass "2" "Schema JSON válido"
    echo "**Resultado:** ✅ PASS" >> "$REPORT_FILE"
else
    gate_fail "2" "Schema inválido"
    echo "**Resultado:** ❌ FAIL" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ═══════════════════════════════════════════════════════════
# GATE 3: Preflight 204
# ═══════════════════════════════════════════════════════════
section "Gate 3/7: Preflight 204 (CORS)"

echo "Comando: curl -X OPTIONS ... (preflight)"
echo ""

PREFLIGHT=$(curl -s -X OPTIONS "$API_URL/v1/machines/$MACHINE_ID/status" \
    -H "Origin: http://localhost:5173" \
    -H "Access-Control-Request-Method: GET" \
    -D - 2>/dev/null | head -20)

cat >> "$REPORT_FILE" <<EOF
### Gate 3: Preflight 204

\`\`\`bash
curl -s -X OPTIONS $API_URL/v1/machines/$MACHINE_ID/status \\
  -H "Origin: http://localhost:5173" -D -
\`\`\`

**Output:**
\`\`\`
$PREFLIGHT
\`\`\`

EOF

GATE3_OK=true
if echo "$PREFLIGHT" | grep -q "HTTP/1.1 204"; then
    echo "  ✓ Status 204 No Content"
else
    echo "  ✗ Status NÃO é 204"
    GATE3_OK=false
fi

if echo "$PREFLIGHT" | grep -qi "access-control-allow-origin:"; then
    echo "  ✓ CORS allow-origin presente"
else
    echo "  ✗ CORS allow-origin ausente"
    GATE3_OK=false
fi

# Verificar se corpo está vazio (Content-Length: 0 ou ausente)
CONTENT_LEN=$(echo "$PREFLIGHT" | grep -i "content-length:" | awk '{print $2}' | tr -d '\r')
if [ -z "$CONTENT_LEN" ] || [ "$CONTENT_LEN" = "0" ]; then
    echo "  ✓ Sem corpo (Content-Length: ${CONTENT_LEN:-ausente})"
else
    echo "  ✗ Corpo presente (Content-Length: $CONTENT_LEN)"
    GATE3_OK=false
fi

if $GATE3_OK; then
    gate_pass "3" "Preflight 204 sem corpo"
    echo "**Resultado:** ✅ PASS" >> "$REPORT_FILE"
else
    gate_fail "3" "Preflight inválido"
    echo "**Resultado:** ❌ FAIL" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ═══════════════════════════════════════════════════════════
# GATE 4: MTConnect /current
# ═══════════════════════════════════════════════════════════
section "Gate 4/7: MTConnect /current"

echo "Comando: curl -s $AGENT_URL/current | xmllint"
echo ""

CURRENT=$(curl -s "$AGENT_URL/current" 2>/dev/null | xmllint --format - 2>/dev/null || echo "")
CURRENT_GREP=$(echo "$CURRENT" | grep -E "RotaryVelocity|PathFeedrate|Execution|units" || echo "")

cat >> "$REPORT_FILE" <<EOF
### Gate 4: MTConnect /current

\`\`\`bash
curl -s $AGENT_URL/current | xmllint --format - | \\
  grep -E "RotaryVelocity|PathFeedrate|Execution|units"
\`\`\`

**Output:**
\`\`\`xml
$CURRENT_GREP
\`\`\`

EOF

GATE4_OK=true
if echo "$CURRENT" | grep -q "RotaryVelocity"; then
    echo "  ✓ RotaryVelocity presente"
elif echo "$CURRENT" | grep -q "SpindleSpeed"; then
    echo "  ⚠ SpindleSpeed (legado, preferir RotaryVelocity)"
    GATE4_OK=false
else
    echo "  ✗ Nenhum RPM data item encontrado"
    GATE4_OK=false
fi

if echo "$CURRENT" | grep -q "PathFeedrate"; then
    echo "  ✓ PathFeedrate presente"
    if echo "$CURRENT" | grep "PathFeedrate" | grep -q 'units="MILLIMETER/SECOND"'; then
        echo "  ✓ PathFeedrate em MILLIMETER/SECOND"
    else
        echo "  ⚠ PathFeedrate com unidade não-padrão"
    fi
else
    echo "  ✗ PathFeedrate ausente"
    GATE4_OK=false
fi

if echo "$CURRENT" | grep -q "Execution"; then
    EXEC=$(echo "$CURRENT" | grep "Execution" | sed 's/<[^>]*>//g' | xargs)
    echo "  ✓ Execution presente: $EXEC"
else
    echo "  ✗ Execution ausente"
    GATE4_OK=false
fi

if $GATE4_OK; then
    gate_pass "4" "MTConnect /current válido"
    echo "**Resultado:** ✅ PASS" >> "$REPORT_FILE"
else
    gate_fail "4" "MTConnect /current incompleto"
    echo "**Resultado:** ❌ FAIL" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ═══════════════════════════════════════════════════════════
# GATE 5: MTConnect /sample (Sequência)
# ═══════════════════════════════════════════════════════════
section "Gate 5/7: MTConnect /sample (Sequência)"

echo "Comando: curl -s $AGENT_URL/sample?count=5"
echo ""

SAMPLE=$(curl -s "$AGENT_URL/sample?count=5" 2>/dev/null | xmllint --format - 2>/dev/null || echo "")
SAMPLE_GREP=$(echo "$SAMPLE" | grep -E "Header|nextSequence|sequence=" || echo "")

cat >> "$REPORT_FILE" <<EOF
### Gate 5: MTConnect /sample

\`\`\`bash
curl -s "$AGENT_URL/sample?count=5" | xmllint --format - | \\
  grep -E "Header|nextSequence|sequence="
\`\`\`

**Output:**
\`\`\`xml
$SAMPLE_GREP
\`\`\`

EOF

GATE5_OK=true
if echo "$SAMPLE" | grep -q "nextSequence"; then
    NEXT_SEQ=$(echo "$SAMPLE" | xmllint --format - | grep -oP 'nextSequence="\K[0-9]+' | head -1)
    echo "  ✓ nextSequence presente: $NEXT_SEQ"
else
    echo "  ✗ nextSequence ausente no Header"
    GATE5_OK=false
fi

SEQUENCES=$(echo "$SAMPLE" | grep -oP 'sequence="\K[0-9]+' || echo "")
if [ -n "$SEQUENCES" ]; then
    echo "  ✓ Amostras com 'sequence' presente"
    echo "    Sequências: $(echo "$SEQUENCES" | head -5 | tr '\n' ' ')"
else
    echo "  ✗ Amostras sem 'sequence'"
    GATE5_OK=false
fi

if $GATE5_OK; then
    gate_pass "5" "MTConnect /sample com sequência"
    echo "**Resultado:** ✅ PASS" >> "$REPORT_FILE"
else
    gate_fail "5" "MTConnect /sample sem sequência"
    echo "**Resultado:** ❌ FAIL" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ═══════════════════════════════════════════════════════════
# GATE 6 e 7: Requerem execução manual (UI + Playwright)
# ═══════════════════════════════════════════════════════════
section "Gate 6/7: UI Dashboard (MANUAL)"

cat >> "$REPORT_FILE" <<EOF
### Gate 6: UI Dashboard

**Execução:** MANUAL

**URL:** http://localhost:5173

**Checklist:**
- [ ] Header visível
- [ ] Machine ID presente
- [ ] 4 cards (RPM, Feed, Estado, Atualizado)
- [ ] Valores atualizam a cada ~2s
- [ ] Cores corretas (verde/vermelho/amarelo)
- [ ] Console sem erros

**Resultado:** ⏳ AGUARDANDO (executar manualmente)

---

EOF

echo ""
echo -e "${YELLOW}⚠️  Gate 6 (UI) requer validação manual:${NC}"
echo "   1. Abrir http://localhost:5173"
echo "   2. Verificar checklist visual"
echo "   3. Capturar screenshot"
echo ""

section "Gate 7/7: Playwright E2E (MANUAL)"

cat >> "$REPORT_FILE" <<EOF
### Gate 7: Playwright E2E

**Comando:**
\`\`\`bash
cd frontend
npx playwright test e2e/status.spec.ts --reporter=list
\`\`\`

**Resultado:** ⏳ AGUARDANDO (executar: \`cd frontend && npx playwright test\`)

---

EOF

echo ""
echo -e "${YELLOW}⚠️  Gate 7 (Playwright) requer execução manual:${NC}"
echo "   cd frontend"
echo "   npx playwright test e2e/status.spec.ts"
echo ""

# ═══════════════════════════════════════════════════════════
# RESUMO FINAL
# ═══════════════════════════════════════════════════════════
section "RESUMO FINAL"

cat >> "$REPORT_FILE" <<EOF
## 📊 Tabela de Aceite

| Gate | Descrição | Status |
|------|-----------|--------|
| 1 | Headers canônicos | $(if [ $PASS -ge 1 ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi) |
| 2 | Schema JSON | $(if [ $PASS -ge 2 ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi) |
| 3 | Preflight 204 | $(if [ $PASS -ge 3 ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi) |
| 4 | MTConnect /current | $(if [ $PASS -ge 4 ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi) |
| 5 | MTConnect /sample | $(if [ $PASS -ge 5 ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi) |
| 6 | UI Dashboard | ⏳ MANUAL |
| 7 | Playwright E2E | ⏳ MANUAL |

---

## 🎯 Veredito Parcial (Gates 1-5)

**Automatizados:** $PASS/5 PASS, $FAIL/5 FAIL

EOF

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "  ${GREEN}✅ PASS: $PASS${NC}  |  ${RED}❌ FAIL: $FAIL${NC}  (Gates 1-5)"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 Gates 1-5 passaram!${NC}"
    echo ""
    echo "Próximos passos:"
    echo "  1. Validar UI (Gate 6): http://localhost:5173"
    echo "  2. Executar Playwright (Gate 7): cd frontend && npx playwright test"
    echo "  3. Preencher campos manuais em $REPORT_FILE"
    echo "  4. Anexar relatório na issue #4"
    echo ""
    cat >> "$REPORT_FILE" <<EOF
**Status:** ✅ Gates automatizados PASS (5/5). Pendente: UI + Playwright.

**Próximo:** Validar Gates 6 e 7 manualmente e anexar na issue #4.
EOF
else
    echo -e "${RED}❌ Alguns gates falharam. Verificar relatório.${NC}"
    echo ""
    cat >> "$REPORT_FILE" <<EOF
**Status:** ❌ $FAIL gate(s) falharam. Corrigir antes de prosseguir.
EOF
    exit 1
fi

echo "📝 Relatório salvo em: $REPORT_FILE"
echo ""

exit 0
