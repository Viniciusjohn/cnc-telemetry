# CNC Telemetry — Deploy Beta em VM Linux

## Resumo
Preparar uma VM Linux pequena para executar o backend FastAPI com SQLite local e expor a API via IP fixo.

## Configuração recomendada da VM
- **IP fixo (exemplo documental):** `200.220.15.10`
- **Porta padrão:** `8000/TCP`
- **Sistema operacional sugerido:** Ubuntu Server LTS 22.04 ou similar
- **Hardware mínimo:** 2 vCPU, 2–4 GB RAM, 20 GB SSD
- **Pacotes básicos:**
  - Python 3.11 + pip
  - Git
  - Node.js + npm (para build do frontend)
  - Nginx (para servir build estático)

## Configurações do backend
- `backend/app/config.py` centraliza `DATABASE_URL`, `API_HOST` e `API_PORT`.
- Variáveis de ambiente aceitas:
  - `TELEMETRY_DATABASE_URL` (ex.: `sqlite:///./telemetry_beta.db`)
  - `TELEMETRY_API_HOST` (padrão `0.0.0.0`)
  - `TELEMETRY_API_PORT` (padrão `8000`)
- Para o piloto, usar SQLite local: `sqlite:///./telemetry_beta.db` (arquivo ficará na pasta backend).

## Firewall / rede
- Liberar apenas a porta `8000/TCP` para acesso externo.
- Restringir o acesso a essa porta ao IP da máquina CNC/cliente sempre que possível.
- Evitar expor outras portas à internet.

## Comandos úteis
1. **Rodar backend na VM:**
   ```bash
   cd /path/to/cnc-telemetry-main/backend
   source .venv/bin/activate  # se existir
   TELEMETRY_DATABASE_URL="sqlite:///./telemetry_beta.db" \
   TELEMETRY_API_HOST="0.0.0.0" \
   TELEMETRY_API_PORT="8000" \
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Teste local rápido:**
   ```bash
   curl http://127.0.0.1:8000/healthz
   ```
   (Se o endpoint ainda não existir, será criado no PROMPT 4.)

3. **URL base da API (exemplo):** `https://200.220.15.10:8000`
   - Planejar uso de HTTPS com certificado self-signed (aceitar alerta no navegador durante o piloto).

## Checklist rápido antes do piloto
- [ ] VM criada com IP público fixo configurado.
- [ ] Porta 8000 liberada apenas para a rede do cliente.
- [ ] Ambiente Python/Node instalado.
- [ ] Repositório clonado nesta VM.
- [ ] Backend sobe com `uvicorn` usando SQLite local.
- [ ] Endpoint `/healthz` responde 200 (será validado após PROMPT 4).
