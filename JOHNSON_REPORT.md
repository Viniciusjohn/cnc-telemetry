# JOHNSON REPORT

## Resumo Executivo
O projeto **CNC Telemetry** provê coleta contínua de dados de máquinas CNC via FastAPI, publica o estado em endpoints REST e alimenta um dashboard React/Vite. A arquitetura prioriza portabilidade em Windows, com scripts para instalação como serviço e simuladores MTConnect.

**Pontos fortes**
- Backend enxuto com domínio bem separado (config, serviços, routers) e pipeline único `M80Adapter → process_m80_snapshot()`.
- Frontend moderno (React 19 + Vite) com polling de status/eventos e componentes especializados (OEE, cartões de telemetria).
- Documentação extensa em `docs/` e scripts Windows/Linux para instalação, diagnósticos e testes de campo.

**Riscos principais**
- Dependência de SQLite/Timescale configurada manualmente, com pouca validação automática de schema.
- Pouca cobertura de testes automatizados em fluxos críticos de ingestão e pipeline M80.
- Observabilidade limitada: logs simples, sem métricas estruturadas ou tracing.

**Próximos passos sugeridos**
1. Automatizar validação do worker M80 na inicialização (health e métricas) e ampliar testes.
2. Consolidar configuração (env/JSON) com documentação única e defaults por ambiente.
3. Investir em suíte de smoke/E2E integrada (backend + frontend) e pipelines CI.

---

## Arquitetura Geral
- **Backend (FastAPI / Python 3.11)**: ponto de entrada em `backend/main.py`, expõe `/v1/telemetry/ingest`, `/v1/machines/*`, histórico e OEE. Worker em `_m80_worker_loop()` chama `backend/app/services/telemetry_pipeline.py` que consulta `M80Adapter` e grava em `Telemetry`/`TelemetryEvents`.
- **Adapter M80**: `backend/app/services/m80_adapter.py` encapsula simulação ou leitura real, fornecendo dados adicionais (spindle load, alarmes). `backend/mtconnect_adapter.py` permanece como cliente MTConnect legado (útil para campo).
- **Frontend (React/Vite)**: `frontend/src/App.tsx` faz polling do backend (status + eventos) e renderiza cartões visuais, com `OEECard` consultando endpoints agregados.
- **Scripts/Tools**: `scripts/` contém simuladores, validadores e scripts de deploy (PowerShell e shell). `install_cnc_telemetry.ps1` instala o backend como serviço / modo demo.

Fluxo crítico (telemetria → UI):
1. `_m80_worker_loop()` chama `process_m80_snapshot()` → `M80Adapter.read_telemetry()` [sim ou real].
2. Pipeline grava snapshot em `Telemetry`, atualiza status e `TelemetryEvents` com extras (spindle load/alarm).
3. Frontend `fetchMachineStatus/Events` consome `/v1/machines/{id}/status|events` e atualiza dashboard.

---

## Mapa de Diretórios
| Diretório | Descrição |
| --- | --- |
| `backend/` | API FastAPI, adapters, serviços, scripts auxiliares, testes e requirements. |
| `frontend/` | Dashboard React/Vite, configurações de build, testes e assets PWA. |
| `scripts/` | Simuladores MTConnect, instaladores auxiliares, scripts bash/PowerShell de validação. |
| `docs/` | Guia completo de campo, planejamento de sprints, checklists e relatórios de gate. |
| `deploy/` | Artefatos específicos de deploy (ex.: configs de VM/Windows). |
| `tools/` | Utilitários de demonstração (ex.: `tools/demo/send_fake_events.py`). |
| `config/` | Arquivos centralizados de configuração (ex.: `alerts.yaml`). |
| `install_cnc_telemetry.ps1` | Instalador one-click do backend como serviço no Windows. |

---

## Inventário de Arquivos Relevantes
| Caminho | Tipo | Papel | Pontos-chave | Crítico |
| --- | --- | --- | --- | --- |
| `backend/main.py` | Python FastAPI | Entrypoint + worker | `_m80_worker_loop`, roteadores, ingest endpoint | ✅ |
| `backend/app/config.py` | Python config | Config central (env + JSON) | Flags `ENABLE_M80_WORKER`, `USE_SIMULATION_DATA`, conexão DB | ✅ |
| `backend/app/db.py` | Python ORM | Engine + modelos `Telemetry`/`TelemetryEvents` | Check constraints, SessionLocal | ✅ |
| `backend/app/services/m80_adapter.py` | Python serviço | Adapter unificado (sim/real) | Simulador `CNCSimulatorLogic`, extras spindle/alarm | ✅ |
| `backend/app/services/telemetry_pipeline.py` | Python serviço | Funil único ingest → status | `_get_adapter`, gravações e chamada `update_status` | ✅ |
| `backend/app/routers/status.py` | Python router | `/v1/machines/{id}` status/eventos | `update_status` persiste metadata extra | ✅ |
| `backend/app/routers/history.py` | Python router | APIs de histórico e agregados | Query Timescale (raw, bucketed) | ✅ |
| `backend/app/routers/oee.py` + `services/oee.py` | Python domínio | Cálculo de OEE por turno/dia | Queries SQL + agregações | ⚠️ |
| `backend/mtconnect_adapter.py` | Python CLI | Adapter MTConnect assíncrono | Poll /sample, ingest HTTP | ⚠️ (campo) |
| `frontend/src/App.tsx` | React | Dashboard principal | Polling status/eventos, layout UI | ✅ |
| `frontend/src/components/OEECard.tsx` | React | Cartão de OEE | Consulta `/v1/machines/{id}/oee` e renders | ⚠️ |
| `scripts/mtconnect_simulator.py` | Python CLI | Simulador MTConnect | Gera /probe,/current,/sample para testes | ⚠️ |
| `install_cnc_telemetry.ps1` | PowerShell | Instalador/serviço Windows | Cria venv, instala deps, registra serviço | ⚠️ |
| `docs/MTConnect_COMPLIANCE.md` | Markdown | Regras canônicas MTConnect | Ajustes RotaryVelocity, PathFeedrate, Execution | ⚠️ |

Legenda: ✅ = lógica crítica de produção, ⚠️ = suporte/infra relevante.

---

## Configuração e Ambientes
- **Backend**: `backend/app/config.py` lê `backend/config.json` + env. Flags importantes: `USE_SIMULATION_DATA`, `ENABLE_M80_WORKER`, `TELEMETRY_POLL_INTERVAL_SEC`, `MACHINE_ID`, `API_URL`, `MACHINE_IP`, `TELEMETRY_DATABASE_URL`.
- **Frontend**: `.env.development` / `.env.production` definem `VITE_API_BASE`, `VITE_MACHINE_ID` etc.
- **Scripts**: `install_cnc_telemetry.ps1` e `scripts/windows/*.ps1` requerem privilégios admin para NSSM/firewall. `config/alerts.yaml` ativa regras do Celery/Redis (alertas).
- **Ambientes**: Não há `.env.example` unificado; documentação em `docs/STATUS_WINDOWS_DEV.md` e `docs/DEPLOY_*`. Dependência forte de variáveis Windows (PowerShell) e JSON em `backend/config.json`.

Fragilidades:
- Segredos/URLs podem ficar hardcoded em JSON/PS1.
- Falta mecanismo para validar config ao subir (ex.: schema, defaults inconsistentes).

---

## Dependências e Stack
### Backend (`backend/requirements.txt`)
- FastAPI 0.104, Uvicorn 0.24 (ASGI server), httpx para clientes, Pydantic v2.
- Banco: SQLAlchemy 2.x, psycopg2-binary, asyncpg, Alembic.
- Alertas: Celery 5.3 + Redis 5 + PyYAML.

### Frontend (`frontend/package.json`)
- React 19 + ReactDOM, Vite (rolldown fork) + TypeScript 5.9.
- Charts: `chart.js` + `react-chartjs-2`.
- Ferramentas: ESLint 9, Playwright 1.56 para e2e.

### Outros
- Scripts PowerShell/Bash exigem Python 3.11+ e `python -m venv` padrão.
- PyInstaller specs: `cnc-telemetry-gateway.spec`, `cnc-telemetry-server.spec`.

---

## Testes e Qualidade
- **Backend**: `backend/tests/` abrange status, histórico/OEE e eventos com fixtures SQLite em memória (`tests/conftest.py`). Ainda não cobre pipeline `M80Adapter` ou ingest loop.
- **Frontend**: `frontend/e2e/smoke.spec.ts` (Playwright) e `frontend/tests/` (não detalhado) – foco em smoke test da UI.
- **Scripts**: `scripts/validate_f2.sh`, `scripts/smoke_f3.sh` atuam como testes manuais/semi-automatizados.
- **CI/CD**: Não há pipelines descritos; execução depende de scripts manuais.

Cobertura faltante:
- Worker `_m80_worker_loop` e `process_m80_snapshot` sem testes automatizados.
- Alertas Celery/Redis, scripts PowerShell e instaladores não são validados.
- Frontend não tem testes unitários/coverage (apenas smoke e e2e). 

---

## Riscos e Pontos Críticos
### Segurança
- **CORS aberto apenas para localhost** (`backend/main.py`), mas ausência de autenticação qualquer nos endpoints (expostos se publicado). Mitigação: adicionar auth/API keys e policies de origem.
- **Segredos em scripts**: `install_cnc_telemetry.ps1` e docs podem pedir execuções com privilégios altos sem controle. Mitigação: instruções claras e assinaturas.

### Confiabilidade
- **Worker M80 sem supervisão**: `_m80_worker_loop` ignora exceções com log simples e não reinicializa adapter se falhar. Mitigação: retry/backoff, health metrics.
- **Piscar DB**: Em `telemetry_pipeline`, rollback silencioso “telemetry insert skipped” pode ocultar falhas. Mitigação: log estruturado + alerta.

### Performance
- **Polling agressivo** (1s) tanto no backend (loop) quanto frontend; sem rate limiting/ batching. Mitigação: permitir configuração de múltiplas máquinas, otimizar queries (índices ok via `TelemetryEvents` indexes).

### Manutenibilidade
- **Frontend monolítico** (`App.tsx` ~500 linhas) com muito inline style. Mitigação: componentizar e usar CSS modules/utility classes.
- **Documentação dispersa**: dezenas de arquivos `EXECUTAR_*`; difícil manter sincronizado. Mitigação: consolidar wiki ou docs site.

### Observabilidade
- Logs `print()` em ingest e pipeline; sem métricas/trace. Mitigação: integrar `structlog`/OpenTelemetry e health endpoints específicos.

### Foco piloto M80 – arquivos e fluxos críticos
- `backend/app/services/m80_adapter.py`: fonte única de snapshots (sim/real). Qualquer regressão aqui afeta alarmes/carga antes de chegar ao pipeline.
- `backend/app/services/telemetry_pipeline.py` + `_m80_worker_loop()` em `backend/main.py`: responsáveis por gravar `Telemetry` e propagar `extra` para `TelemetryEvents`/status. Falhas silenciosas perdem o batimento cardíaco do piloto.
- `backend/app/routers/status.py` e `history.py`: alimentam a UI com último estado e log; precisam continuar coerentes com `TelemeteryEvents`.
- `frontend/src/App.tsx` e `frontend/src/components/OEECard.tsx`: únicos consumidores visíveis no piloto; qualquer alteração de contrato quebra o monitoramento.

**Riscos específicos**
1. **Adapter/worker em modo silencioso**: hoje só há logs `warning`/`info`. Se o worker travar, o piloto perde dados sem alerta. Mitigação: watchdog com métricas mais alarme visual na UI.
2. **Contrato status/eventos**: mudanças na forma como `update_status` grava `spindle_load_pct`/`alarm_code` podem quebrar `fetchMachineStatus/Events`. Mitigação: travar schema via testes.
3. **UI rígida**: `App.tsx` assume `MACHINE_ID` fixo e polling a cada 1s; múltiplas máquinas exigirão revisitar esse fluxo antes do piloto multi-site.

---

## Próximos Passos Técnicos
1. **Automação de testes críticos**: adicionar testes para `process_m80_snapshot`, worker startup, e um e2e backend+frontend (pode usar Playwright hitting FastAPI em simulação).
2. **Observabilidade/monitoramento**: registrar métricas do worker (último timestamp, erros consecutivos) e expor em `/healthz`.
3. **Higiene de configuração**: fornecer `.env.example`, validar `config.json` vs env, documentar flags em um único guia.
4. **Melhorias de segurança**: autenticação básica ou API tokens para ingest e status; revisão de scripts PowerShell (assinar, validar).
5. **Refatoração frontend**: dividir `App.tsx` em páginas/composições menores e adicionar testes unitários para componentes críticos.
