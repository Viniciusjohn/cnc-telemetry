# CNC Telemetry — Deploy Beta em Windows 10/11

Guia para subir o backend FastAPI (SQLite) e o frontend Vite em uma máquina Windows 10/11 (Pro ou Enterprise) usada como VM de staging/piloto.

## 1. Pré-requisitos
- Windows 10/11 atualizado.
- Permissão de Administrador para instalar pacotes.
- PowerShell 7+ recomendado.
- Conectividade com a rede da máquina CNC.

### Pacotes mínimos (via PowerShell/winget)
```powershell
winget install -e --id Python.Python.3.11
winget install -e --id Git.Git
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id Microsoft.Nginx  # opcional; use outro servidor se preferir
```
> Se `winget` não estiver disponível, baixe manualmente dos sites oficiais.

## 2. Estrutura de pastas
Este guia assume o código em `C:\cnc-telemetry-main`. Ajuste os caminhos se usar outro diretório.

## 3. Backend (FastAPI + SQLite)
```powershell
# 1. Clonar/atualizar repo
cd C:\
git clone https://example.com/cnc-telemetry-main.git
cd C:\cnc-telemetry-main
# git pull   # se já existir

# 2. Criar venv e instalar deps
cd backend
"C:\Program Files\Python311\python.exe" -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 3. Configurar .env (SQLite local)
@"
TELEMETRY_DATABASE_URL=sqlite:///./telemetry_beta.db
TELEMETRY_API_HOST=0.0.0.0
TELEMETRY_API_PORT=8000
"@ | Out-File -Encoding UTF8 .env.beta

# 4. Seed opcional
python -m scripts.seed_beta_demo

# 5. Rodar backend (teste manual)
uvicorn main:app --host 0.0.0.0 --port 8000
```
> Pressione `Ctrl+C` para parar o teste manual. Para rodar em background permanente use NSSM ou `sc create` (ver seção 5).

## 4. Frontend (Vite)
```powershell
cd C:\cnc-telemetry-main\frontend
npm install
npm run build
```
Saída: `C:\cnc-telemetry-main\frontend\dist`.

### Servir o build
Opções:
1. **Nginx para Windows** (instalado via winget). Configure `nginx.conf` apontando `root` para `C:/cnc-telemetry-main/frontend/dist` (veja exemplo em `docs/FRONTEND_DEPLOY_VM.md`).
2. **Servidor simples para staging**:
   ```powershell
   npx serve -s dist --listen 0.0.0.0:4173
   ```
   Use apenas para testes rápidos; não recomendado para produção prolongada.

## 5. Serviço Windows (backend)
Para manter o backend ativo após logoff, use **NSSM** (Non-Sucking Service Manager):
```powershell
winget install -e --id NSSM.NSSM
nssm install cnc-telemetry-backend "C:\cnc-telemetry-main\backend\.venv\Scripts\uvicorn.exe" "main:app" --host 0.0.0.0 --port 8000
nssm set cnc-telemetry-backend AppDirectory C:\cnc-telemetry-main\backend
nssm set cnc-telemetry-backend AppEnvironmentExtra TELEMETRY_DATABASE_URL=sqlite:///./telemetry_beta.db
nssm set cnc-telemetry-backend AppEnvironmentExtra TELEMETRY_API_HOST=0.0.0.0
nssm set cnc-telemetry-backend AppEnvironmentExtra TELEMETRY_API_PORT=8000
nssm start cnc-telemetry-backend
```
Alternativa sem NSSM: criar um serviço com `sc create` chamando um script PowerShell que ativa o venv e executa `uvicorn`. NSSM é mais simples para o piloto.

## 6. Checklist pós-deploy
1. Backend ativo (`nssm status cnc-telemetry-backend` ou verificar processo `uvicorn`).
2. `curl http://127.0.0.1:8000/healthz` responde `{ "status": "ok" }`.
3. Frontend servindo em `https://<IP-VM>/` (ou porta configurada); aceitar certificado self-signed.
4. Se rodou o seed, `/status` e dashboard mostram máquina `SIM_M80_01` com dados sintéticos.
5. Se rebootar a VM, o serviço NSSM deve reiniciar automaticamente; confirme com `nssm status` e `curl /healthz`.

## 7. Comandos de validação (PowerShell)
```powershell
curl http://localhost:8000/healthz
curl http://localhost:8000/v1/machines/SIM_M80_01/status
curl "http://localhost:8000/v1/machines/SIM_M80_01/events?limit=5"
curl "http://localhost:8000/v1/machines/SIM_M80_01/history?resolution=raw&limit=10"
curl http://localhost:8000/v1/machines/SIM_M80_01/oee
```
Para o painel, abra o navegador em `https://<IP-VM>/` (ou `http://localhost:4173` se usando `npx serve`).

## 8. Troubleshooting rápido
| Sintoma | Ação |
| --- | --- |
| `uvicorn` não sobe | Verifique se o venv está ativo e se o serviço NSSM aponta para o executável correto. |
| Porta 8000 ocupada | Rode `netstat -ano | findstr 8000` e finalize o processo conflitando. |
| Nginx não inicia | Use `nginx -t` para validar o config e cheque se a porta 443/80 já está em uso. |
| Painel sem dados | Certifique-se de que o seed rodou ou que a CNC está publicando para o IP da VM. |

Seguindo este roteiro, o ambiente Windows replica o fluxo Linux do piloto, com backend FastAPI + SQLite e frontend estático servidos localmente.
