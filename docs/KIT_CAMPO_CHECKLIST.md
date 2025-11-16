# Kit de Campo — CNC Telemetry Beta

Checklist do que deve ir para a fábrica antes do piloto.

## 1. Documentação impressa/PDF
- docs/DEPLOY_BETA_VM.md
- docs/DEPLOY_BETA_WINDOWS.md
- docs/FRONTEND_DEPLOY_VM.md
- docs/OPERACAO_BETA_CAMPO.md
- docs/TROUBLESHOOTING_BETA.md

> Exportar para PDF ou imprimir. Revisar destaque para portas (8000/TCP) e certificados self-signed.

## 2. Scripts e serviços
- deploy/deploy_beta_vm.sh (validar URL real do repositório antes de copiar)
- deploy/cnc-telemetry.service.example
- NSSM installer (se não houver internet no cliente)

## 3. Artefatos técnicos
- frontend/dist (zipar como `frontend_dist.zip`)
- backend/.env.beta (modelo, sem credenciais sensíveis)
- Backup de `backend/telemetry_beta.db` com seed (renomear para `telemetry_beta_seed.db`)
- Hash/commit do repositório utilizado no staging (anotar em README do kit)

## 4. Softwares auxiliares (caso o cliente não possua)
- Instaladores offline: Python 3.11, Node.js LTS, Git, NSSM, Nginx.
- Ferramentas de diagnóstico: `curl` para Windows (se faltar) ou instruções de uso do PowerShell Invoke-WebRequest.

## 5. Comandos resumidos para colar em campo
### Linux
```
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip git nodejs npm nginx
cd /opt && git clone <URL_REAL_DO_REPO> cnc-telemetry-main && cd cnc-telemetry-main
bash deploy/deploy_beta_vm.sh
sudo systemctl status cnc-telemetry
curl http://127.0.0.1:8000/healthz
```

### Windows
```
winget install -e --id Python.Python.3.11 Git.Git OpenJS.NodeJS.LTS NSSM.NSSM
cd C:\ && git clone <URL_REAL_DO_REPO> cnc-telemetry-main
cd C:\cnc-telemetry-main\backend && "C:\\Program Files\\Python311\\python.exe" -m venv .venv
.\.venv\Scripts\activate && python -m pip install -r requirements.txt && python -m scripts.seed_beta_demo && deactivate
cd ..\frontend && npm install && npm run build
nssm install cnc-telemetry-backend "C:\\cnc-telemetry-main\\backend\\.venv\\Scripts\\uvicorn.exe" main:app --host 0.0.0.0 --port 8000
nssm start cnc-telemetry-backend
curl http://localhost:8000/healthz
```

## 6. Verificações finais antes de empacotar
- [ ] deploy_beta_vm.sh atualizado com URL do repositório.
- [ ] frontend_dist.zip testado (`npx serve -s dist`).
- [ ] `telemetry_beta_seed.db` validado (abrir com sqlite3 e conferir tabelas).
- [ ] Todos os PDFs no pendrive + pasta compartilhada.
- [ ] Planilha de contatos (Nestor, equipe de TI do cliente) anexada.

Assim, o time leva tudo o que precisa para reinstalar rapidamente mesmo sem internet no local.
