# Estado Atual do Projeto - CNC-Genius Telemetria v0.2

## Resumo da Implementação

### Arquivo da Página Principal do Dashboard
- **Localização**: `c:\cnc-telemetry-main\frontend\src\App.tsx`
- **Descrição**: Componente React principal com layout v0.1 implementado

### Arquivo/Função que Faz o Fetch dos Dados
- **API Client**: `c:\cnc-telemetry-main\frontend\src\lib\api.ts`
- **Funções**: 
  - `fetchMachineStatus(machineId: string)` - Status atual
  - `fetchMachineEvents(machineId: string, limit: number)` - Histórico de eventos v0.2
- **Endpoints**: 
  - `GET /v1/machines/{machine_id}/status` - Status atual
  - `GET /v1/machines/{machine_id}/events` - Eventos históricos v0.2
- **Backend**: `c:\cnc-telemetry-main\backend\app\routers\status.py`

### Estrutura Atual do Payload (JSON v0.1)

```json
{
  "machine_id": "SIM_M80_01",
  "controller_family": "MITSUBISHI_M8X",
  "timestamp_utc": "2025-11-13T10:00:00Z",
  "mode": "AUTOMATIC",
  "execution": "EXECUTING",
  "rpm": 3500,
  "feed_rate": 1200,
  "spindle_load_pct": 52,
  "tool_id": "T03",
  "alarm_code": "105",
  "alarm_message": "OVERTRAVEL +X",
  "part_count": 145,
  "update_interval_ms": 1000,
  "source": "mtconnect:sim"
}
```

## Implementações Concluídas

### ✅ Branding CNC-Genius Telemetria
- Título da página: "CNC-Genius Telemetria"
- Header principal: "CNC-Genius Telemetria"
- Subtítulo: "Monitoramento em tempo real • Atualização a cada 1s"
- README.md atualizado

### ✅ Contrato JSON v0.1 Canônico
- Backend adaptado para retornar formato v0.1
- Mapeamento de campos legados para novos campos
- Campos opcionais tolerantes a null
- Adapter layer implementado

### ✅ Layout v0.1 Dashboard
**Linha Superior (3 cards grandes):**
- RPM (com cor baseada no estado de execução)
- FEED (mm/min)
- ESTADO (RODANDO/PARADA/PRONTA)

**Linha Inferior (4 cards menores):**
- MODO (AUTO/MANUAL)
- LOAD (%) (com tratamento de null)
- FERRAMENTA (ID da ferramenta ou "—")
- ALARME (card especial com 2 linhas)

### ✅ Polling 1s + Estado de Conexão
- Intervalo de polling: 1000ms (1 segundo)
- Badge de status de conexão:
  - **Conectado**: dados atualizados
  - **Sinal instável**: atraso > 3s
  - **Sem atualização**: erro de conexão

### ✅ Tolerância a Null
- Todos os campos opcionais tratam null graciosamente
- Placeholders "—" para valores ausentes
- UI não quebra com dados incompletos

## Arquivos Modificados

1. **Frontend**:
   - `frontend/index.html` - título atualizado
   - `frontend/src/App.tsx` - layout v0.1 + branding + polling 1s
   - `frontend/src/lib/api.ts` - interface atualizada para v0.1

2. **Backend**:
   - `backend/app/routers/status.py` - modelo v0.1 + adapter

3. **Documentação**:
   - `README.md` - branding atualizado
   - `docs/DECISOES_ARQUITETURA.md` - decisões técnicas
   - `docs/ESTADO_ATUAL.md` - este arquivo

## Próximos Passos

O projeto está pronto para testes com dados reais. A base está sólida para:
- Integração com MTConnect real
- Expansão de campos de telemetria
- Consumo por outros módulos (CNC-Genius, app Android)

## Notas Técnicas

- **Polling estável**: 1s fixo conforme especificação
- **Backward compatibility**: funções legadas mantidas
- **Null safety**: todos os componentes robustos contra dados ausentes
- **Responsive design**: layout adapta-se a diferentes resoluções

## v0.3 – Qualidade & Deploy

- **Resumo**: Python 3.11 passa a ser o padrão oficial da stack, garantindo compatibilidade dos wheels e alinhamento com o setup Windows; o backend ganha uma suite Pytest mínima; o foco da v0.3 é estender isso para CI, Docker Compose e segurança leve (API key opcional).
- **Por quê**: Sem travar versão e testes básicos, qualquer alteração em /status, /events, /history ou /oee pode quebrar em silêncio antes de chegar ao M80/NovaTEC.
- **Como validar**: pytest no backend precisa passar localmente (venv 3.11) cobrindo contrato JSON v0.1 e shapes de eventos/histórico/OEE; nas próximas entregas, GitHub Actions (Py 3.11 + Node) e docker compose devem replicar isso automaticamente.
- **Riscos**: Fixtures mal isoladas podem usar o banco real; testes tentando validar matemática detalhada tornam a suite frágil.
- **Próximo passo**: Implementar a suite Pytest descrita no plano e, em seguida, avançar para smoke do frontend, CI e Docker Compose.

