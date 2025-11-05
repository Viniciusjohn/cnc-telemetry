# 📄 Template Relatório PoC — CNC Telemetry

**Cliente:** [Nome da Empresa]  
**Máquina:** [Série/Modelo]  
**Data:** [DD/MM/YYYY]  
**Duração:** 2 horas (PoC mínimo)

---

## Cenário Antes (Manual)

- ❌ Sem visibilidade de status remoto
- ❌ Downtime desconhecido (descoberto apenas ao final do turno)
- ❌ OEE estimado: ~60-70% (sem medição real)
- ❌ Alertas: apenas quando operador percebe
- ❌ Relatórios manuais (Excel, erro humano)

---

## Cenário Depois (CNC Telemetry)

- ✅ Dashboard em tempo real (atualização 2s)
- ✅ Histórico 30 dias (queries < 2s)
- ✅ Alertas automáticos (Slack, < 5s latência)
- ✅ OEE medido: **68.4%** (dado real)
- ✅ Relatórios automáticos (CSV/PDF)

---

## Métricas Coletadas (2h PoC)

| Métrica | Valor | Observação |
|---------|-------|------------|
| **Tempo Total** | 120 min | 2h de teste |
| **Tempo Executando** | 82 min | 68.3% |
| **Tempo Parado** | 28 min | 23.3% |
| **Tempo Idle** | 10 min | 8.3% |
| **RPM Médio** | 4250 | Programado: 4500 |
| **Feed Médio** | 1180 mm/min | Programado: 1200 |
| **Alertas Disparados** | 2 | Paradas >60s |
| **Perda de Dados** | 0.1% | < 0.5% target ✓ |

---

## OEE Calculado

**Fórmula:** `OEE = Availability × Performance × Quality`

- **Availability:** 68.3% (82 min / 120 min)
- **Performance:** 94.4% (4250 RPM / 4500 RPM)
- **Quality:** 100% (assumido)
- **OEE:** **64.5%**

**Benchmark Industrial:**
- < 60%: ❌ Inaceitável
- 60-70%: ⚠️ Razoável
- 70-85%: ✅ Competitivo
- \> 85%: 🏆 World Class

**Meta:** Aumentar para 75%+ em 30 dias

[Ref: OEE Calculation](https://www.oee.com/)

---

## ROI Projetado (10 CNCs)

**Premissas:**
- 10 máquinas CNC
- 2 turnos/dia (16h)
- 22 dias úteis/mês

### Ganho 1: Reduzir Setup Time (20%)
- Setup atual: 4h/dia
- Redução: 0.8h/dia × 22 dias = **17.6h/mês**
- Valor/hora operador: R$ 200
- **Economia: R$ 3.520/mês**

### Ganho 2: Aumentar OEE (65% → 75%)
- Throughput extra: 10% × 22 dias × 10 máquinas
- Receita/peça: R$ 50
- Peças/dia/máquina: 100
- **Receita extra: R$ 11.000/mês**

### Cálculo ROI
- **Ganho Total:** R$ 14.520/mês
- **Custo CNC Telemetry:** R$ 990/mês (10 × R$ 99)
- **ROI:** 1367%
- **Payback:** 2 dias

---

## Prints (Screenshots)

### Dashboard Real-Time
\![Dashboard](screenshots/dashboard.png)
- Status: Executando (verde)
- RPM: 4250
- Feed: 1180 mm/min
- Última atualização: 2s atrás

### Histórico 24h
\![Histórico](screenshots/historico_24h.png)
- Gráfico de linha: RPM ao longo do tempo
- Picos e vales identificados
- Paradas marcadas em vermelho

### Alerta Slack
\![Alerta](screenshots/alerta_slack.png)
```
🔴 ABR-850 parada há 12 min
Estado: stopped
RPM: 0
Feed: 0 mm/min
Timestamp: 2025-11-05 10:23:15
```

---

## Próximos Passos

1. ✅ Aprovar proposta comercial (R$ 99/máquina/mês)
2. ✅ Assinar contrato mensal (cancelável anytime)
3. ✅ Agendar instalação em 10 CNCs (1 dia)
4. ✅ Treinamento equipe (2h presencial)
5. ✅ Go-live + suporte 24/7 (Slack)

---

## Assinaturas

**Cliente:**  
___________________________  
[Nome]  
Data: ___/___/______

**CNC Telemetry:**  
___________________________  
Vinicius John  
Data: ___/___/______

---

**Anexos:**
- Proposta comercial detalhada
- Contrato de prestação de serviços
- Manual de uso (PDF)
