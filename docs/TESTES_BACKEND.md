# TESTES BACKEND

## Resumo
Existe agora uma suíte Pytest mínima garantindo que os endpoints principais do backend (/status, /events, /history, /oee) mantenham o contrato de payload combinado para o M80/NovaTEC.
Os testes rodam em segundos usando FastAPI TestClient e um banco SQLite em memória, protegendo o fluxo básico de telemetria.

## Por quê
Evitar regressões silenciosas no contrato JSON (v0.1/v0.2) antes de avançar com CI, Docker e deploy — qualquer alteração crítica grita no pytest.

## Seed beta demo
- Script: `backend/scripts/seed_beta_demo.py`
- Rodar via módulo para respeitar PYTHONPATH:
  ```powershell
  cd C:\cnc-telemetry-main\backend
  python -m scripts.seed_beta_demo
  ```
- O seed cria máquina `SIM_M80_01`, alguns pontos de telemetria e eventos para smoke tests locais.

## Como validar
```powershell
cd C:\cnc-telemetry-main\backend
python -m pytest -vv
```
Resultado esperado: todos os testes PASS (status 0). Qualquer falha indica quebra no contrato dos endpoints monitorados.

### Última execução
- Data: 2025-11-15
- Comando: `python -m pytest -vv`
- Resultado: ✅ SUITE VERDE (6 testes)

## Riscos
- [ASSUNCAO] A suíte usa SQLite em memória; diferenças específicas de Postgres/Timescale (ex.: tipos de data/hora ou funções Timescale) não são cobertas.
- Seeds sintéticos simples podem não refletir casos extremos do chão de fábrica.

## Próximo passo
Expandir a cobertura para cenários negativos (404, máquina inexistente, limites inválidos) e integrar a execução ao CI (GitHub Actions) para travar merges quebrados.
