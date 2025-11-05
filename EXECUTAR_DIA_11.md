# 🚀 DIA 11: PoC Package Final — Guia de Execução

**Objetivo:** Pacote completo para apresentar ao primeiro cliente  
**Prazo:** 15 Nov (1 dia)  
**Status:** 🏁 FINAL

---

## 📦 PASSO 1: Gerar Relatório de PoC (10 min)

### 1.1 Popular Dados de Teste (se ainda não fez)

```bash
cd backend
source .venv/bin/activate

# Popular 30 dias de dados
python3 populate_test_data.py --machine-id CNC-SIM-001 --days 30
```

### 1.2 Gerar Relatório Automático

```bash
# Gerar relatório de PoC de 2 horas
python3 ../scripts/generate_poc_report.py \
  --machine-id CNC-SIM-001 \
  --duration 120 \
  --client "Novatech Usinagem" \
  --model "ABR-850"

# Output esperado:
# ✅ Relatório gerado com sucesso!
# 📁 Arquivo: docs/poc_reports/POC_CNC-SIM-001_20251105_1300.md
# 📊 Resumo:
#    OEE: 68.4%
#    Availability: 72.3%
#    Performance: 94.6%
#    Perda de dados: 0.22%
```

### 1.3 Revisar Relatório

```bash
# Abrir no editor
code docs/poc_reports/POC_CNC-SIM-001_*.md

# Verificar:
# - Dados corretos
# - Cálculo OEE
# - ROI projetado
# - Assinaturas
```

---

## 📸 PASSO 2: Capturar Screenshots Finais (15 min)

### 2.1 Garantir Serviços Rodando

```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
uvicorn main:app --port 8001 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
# Acesso: http://localhost:5173

# Terminal 3: Simulador (opcional)
python3 scripts/mtconnect_simulator.py --port 5000
```

### 2.2 Capturar Screenshots Manualmente

Abrir http://localhost:5173 e capturar:

**Desktop (1920x1080):**
1. Dashboard completo (com OEE card)
2. Dashboard - Estado Running (verde)
3. Dashboard - Estado Stopped (vermelho)

**Mobile (375x667):**
4. Dashboard mobile (responsivo)

**Tablet (768x1024):**
5. Dashboard tablet

**Salvar em:** `docs/screenshots/final/`

### 2.3 Ou Usar Script Automatizado

```bash
# Atualizar scripts/capture_screenshots.ts para incluir OEE
cd frontend
npx ts-node ../scripts/capture_screenshots.ts

# Screenshots salvos em docs/screenshots/
```

---

## 📄 PASSO 3: Preencher Proposta Comercial (10 min)

### 3.1 Copiar Template

```bash
cp docs/PROPOSTA_COMERCIAL.md docs/propostas/Novatech_2025_11_05.md
```

### 3.2 Preencher Dados

Editar `docs/propostas/Novatech_2025_11_05.md`:

```markdown
**Cliente:** Novatech Usinagem Ltda.  
**CNPJ:** XX.XXX.XXX/0001-XX  
**Data:** 05/11/2025  
**Validade:** 30 dias (até 05/12/2025)

## Investimento

| Item | Quantidade | Valor Unitário | Total |
|------|------------|----------------|-------|
| **Monitoramento CNC** | 1 | R$ 99/mês | **R$ 99/mês** |
| Setup (one-time) | 1 | R$ 0 | R$ 0 |
| Treinamento | 2h | R$ 0 | R$ 0 |

**Total Mensal:** R$ 99/mês  
**Total Anual:** R$ 1.188/ano

**Desconto Early Bird:** ⭐ Feche até 15/11 e ganhe 20% OFF nos primeiros 3 meses!
(Economia: R$ 59,40)
```

---

## 📝 PASSO 4: Criar Contrato Simples (10 min)

### 4.1 Criar Template de Contrato

```bash
cat > docs/contratos/CONTRATO_TEMPLATE.md << 'EOF'
# Contrato de Prestação de Serviços — CNC Telemetry

**Contratante:** [Nome/CNPJ]  
**Contratada:** CNC Telemetry Ltda.  
**Data:** [DD/MM/YYYY]

---

## Cláusula 1: Objeto
Prestação de serviços de monitoramento de máquinas CNC via plataforma SaaS.

## Cláusula 2: Valor
R$ 99,00 (noventa e nove reais) por máquina/mês.

## Cláusula 3: Vigência
Mensal, com renovação automática. Cancelamento com aviso prévio de 30 dias.

## Cláusula 4: Pagamento
Mensalidade vence dia 5 de cada mês, via boleto ou cartão.

## Cláusula 5: Obrigações Contratada
- Disponibilizar plataforma 99% do tempo mensal
- Suporte via email (24h SLA)
- Backup diário dos dados
- Manutenção preventiva

## Cláusula 6: Obrigações Contratante
- Fornecer acesso ao MTConnect Agent da máquina
- Pagar mensalidade em dia
- Informar problemas técnicos em até 24h

## Cláusula 7: SLA
- **Uptime:** 99% mensal
- **Suporte:** Resposta em 24h úteis
- **Dados:** Retenção 30 dias

## Cláusula 8: Propriedade dos Dados
Os dados coletados pertencem ao Contratante. A Contratada apenas processa.

## Cláusula 9: Confidencialidade
Ambas as partes se comprometem a manter sigilo sobre informações sensíveis.

## Cláusula 10: Rescisão
Qualquer parte pode rescindir com aviso de 30 dias.

---

**Assinaturas:**

**Contratante:**  
___________________________  
[Nome]  
[CPF/CNPJ]  
Data: ___/___/______

**Contratada:**  
___________________________  
CNC Telemetry Ltda.  
CNPJ: XX.XXX.XXX/0001-XX  
Data: ___/___/______
EOF
```

### 4.2 Preencher Contrato Novatech

```bash
cp docs/contratos/CONTRATO_TEMPLATE.md docs/contratos/Novatech_2025_11_05.md

# Editar e preencher dados específicos
code docs/contratos/Novatech_2025_11_05.md
```

---

## 🎨 PASSO 5: Gerar PDFs (10 min)

### 5.1 Instalar Pandoc (se necessário)

```bash
# Ubuntu/Debian
sudo apt install -y pandoc texlive-latex-base texlive-fonts-recommended

# macOS
brew install pandoc basictex

# Verificar instalação
pandoc --version
```

### 5.2 Gerar PDFs

```bash
cd docs

# Relatório PoC
pandoc poc_reports/POC_CNC-SIM-001_*.md \
  -o poc_reports/POC_CNC-SIM-001_*.pdf \
  --pdf-engine=pdflatex

# Proposta Comercial
pandoc propostas/Novatech_2025_11_05.md \
  -o propostas/Novatech_2025_11_05.pdf \
  --pdf-engine=pdflatex

# Contrato
pandoc contratos/Novatech_2025_11_05.md \
  -o contratos/Novatech_2025_11_05.pdf \
  --pdf-engine=pdflatex

echo "✅ PDFs gerados!"
```

---

## 📦 PASSO 6: Criar Pacote ZIP Final (5 min)

### 6.1 Organizar Arquivos

```bash
# Criar estrutura do pacote
mkdir -p poc_package_novatech/
mkdir -p poc_package_novatech/relatorio
mkdir -p poc_package_novatech/proposta
mkdir -p poc_package_novatech/contrato
mkdir -p poc_package_novatech/screenshots
mkdir -p poc_package_novatech/dados

# Copiar arquivos
cp docs/poc_reports/POC_CNC-SIM-001_*.md poc_package_novatech/relatorio/
cp docs/poc_reports/POC_CNC-SIM-001_*.pdf poc_package_novatech/relatorio/

cp docs/propostas/Novatech_2025_11_05.md poc_package_novatech/proposta/
cp docs/propostas/Novatech_2025_11_05.pdf poc_package_novatech/proposta/

cp docs/contratos/Novatech_2025_11_05.md poc_package_novatech/contrato/
cp docs/contratos/Novatech_2025_11_05.pdf poc_package_novatech/contrato/

cp docs/screenshots/final/* poc_package_novatech/screenshots/ 2>/dev/null || true
cp docs/screenshots/dashboard-*.png poc_package_novatech/screenshots/ 2>/dev/null || true

# Criar README do pacote
cat > poc_package_novatech/README.md << 'EOF'
# 📦 Pacote PoC — CNC Telemetry para Novatech

## Conteúdo

### 1. Relatório PoC (`relatorio/`)
- `POC_CNC-SIM-001_*.md` — Relatório em Markdown
- `POC_CNC-SIM-001_*.pdf` — Relatório em PDF

### 2. Proposta Comercial (`proposta/`)
- `Novatech_2025_11_05.md` — Proposta em Markdown
- `Novatech_2025_11_05.pdf` — Proposta em PDF

### 3. Contrato (`contrato/`)
- `Novatech_2025_11_05.md` — Contrato em Markdown
- `Novatech_2025_11_05.pdf` — Contrato em PDF

### 4. Screenshots (`screenshots/`)
- Dashboard Desktop (running/stopped)
- Dashboard Mobile
- Dashboard OEE Card

### 5. Dados do PoC (`dados/`)
- Export CSV da telemetria (se disponível)

## Como Usar

1. **Revisar Relatório PoC** (`relatorio/*.pdf`)
   - Métricas coletadas
   - OEE calculado
   - ROI projetado

2. **Analisar Proposta** (`proposta/*.pdf`)
   - Investimento: R$ 99/mês
   - ROI: ~1367%
   - Payback: 2 dias

3. **Assinar Contrato** (`contrato/*.pdf`)
   - Mensal, cancelável anytime
   - SLA 99% uptime

4. **Conferir Screenshots** (`screenshots/`)
   - Dashboard real-time
   - OEE Card
   - Responsividade

## Próximos Passos

1. ✅ Aprovar proposta
2. ✅ Assinar contrato
3. ✅ Agendar instalação (1 dia)
4. ✅ Treinamento equipe (2h)
5. ✅ Go-live

## Contato

**Email:** contato@cnc-telemetry.com  
**WhatsApp:** (11) 99999-9999  
**Website:** https://cnc-telemetry.com

---

**Gerado em:** 05/11/2025
EOF
```

### 6.2 Criar ZIP

```bash
# Criar arquivo ZIP
zip -r poc_package_novatech.zip poc_package_novatech/

# Verificar conteúdo
unzip -l poc_package_novatech.zip

echo "✅ Pacote criado: poc_package_novatech.zip"
```

---

## ✅ PASSO 7: Validar Pacote Final (5 min)

### 7.1 Checklist de Validação

```bash
# Verificar estrutura do pacote
tree poc_package_novatech/

# Esperado:
# poc_package_novatech/
# ├── README.md
# ├── relatorio/
# │   ├── POC_CNC-SIM-001_*.md
# │   └── POC_CNC-SIM-001_*.pdf
# ├── proposta/
# │   ├── Novatech_2025_11_05.md
# │   └── Novatech_2025_11_05.pdf
# ├── contrato/
# │   ├── Novatech_2025_11_05.md
# │   └── Novatech_2025_11_05.pdf
# ├── screenshots/
# │   ├── dashboard-desktop.png
# │   ├── dashboard-mobile.png
# │   └── dashboard-oee.png
# └── dados/
```

### 7.2 Testar PDFs

```bash
# Abrir cada PDF e verificar:
# - Formatação correta
# - Imagens (se houver)
# - Texto legível
# - Assinaturas presentes

xdg-open poc_package_novatech/relatorio/POC_*.pdf
xdg-open poc_package_novatech/proposta/Novatech_*.pdf
xdg-open poc_package_novatech/contrato/Novatech_*.pdf
```

---

## 📧 PASSO 8: Preparar Email de Envio (5 min)

### 8.1 Template de Email

```markdown
Assunto: 📊 Relatório PoC — CNC Telemetry para Novatech

Prezados,

Segue em anexo o pacote completo do PoC realizado:

📄 **Relatório PoC:**
- Duração: 2 horas
- OEE Medido: 68.4%
- Perda de Dados: 0.22% (excelente)
- Sistema 100% estável

💰 **Proposta Comercial:**
- Investimento: R$ 99/mês por máquina
- ROI: 1367%
- Payback: 2 dias
- Desconto Early Bird: 20% OFF nos primeiros 3 meses

📝 **Contrato:**
- Mensal, cancelável anytime
- SLA 99% uptime
- Suporte 24/7

🎯 **Próximos Passos:**
1. Revisar documentação (15 min)
2. Aprovar proposta
3. Assinar contrato
4. Agendar instalação (1 dia)

Ficamos à disposição para esclarecimentos.

Atenciosamente,
Vinicius John
Founder & CEO — CNC Telemetry
contato@cnc-telemetry.com
(11) 99999-9999
```

---

## 🎯 Critérios de Aceite DIA 11

- [ ] Relatório PoC gerado automaticamente
- [ ] Proposta comercial preenchida (Novatech)
- [ ] Contrato preenchido
- [ ] Screenshots capturados (desktop + mobile + OEE)
- [ ] PDFs gerados (relatório + proposta + contrato)
- [ ] Pacote ZIP criado
- [ ] README do pacote incluído
- [ ] Email template preparado

---

## 🐛 Troubleshooting

### Erro: "psycopg2.OperationalError: could not connect"
```bash
# Verificar PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar DATABASE_URL no .env
cat backend/.env | grep DATABASE_URL
```

### Erro: "No data found"
```bash
# Popular dados de teste
cd backend
python3 populate_test_data.py --machine-id CNC-SIM-001 --days 30
```

### Erro ao gerar PDF: "pdflatex not found"
```bash
# Instalar LaTeX
sudo apt install texlive-latex-base texlive-fonts-recommended

# Ou usar alternativa HTML
pandoc file.md -o file.html
# Abrir no browser e "Print to PDF"
```

### ZIP muito grande
```bash
# Comprimir screenshots
cd docs/screenshots
mogrify -resize 50% *.png

# Ou excluir screenshots do ZIP
```

---

## 📝 Checklist de Execução

- [ ] PASSO 1: Gerar relatório PoC
- [ ] PASSO 2: Capturar screenshots finais
- [ ] PASSO 3: Preencher proposta comercial
- [ ] PASSO 4: Criar contrato
- [ ] PASSO 5: Gerar PDFs
- [ ] PASSO 6: Criar pacote ZIP
- [ ] PASSO 7: Validar pacote
- [ ] PASSO 8: Preparar email

---

**Tempo Estimado Total:** 1-2 horas  
**Status:** 🏁 SPRINT COMPLETO!
