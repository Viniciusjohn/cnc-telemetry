# CNC Telemetry — Operação Beta em Campo

Checklist para o time levar o piloto até a fábrica sem surpresas.

## Bloco A — Antes de sair de casa
1. `python -m pytest -vv` no backend (garantir SUITE VERDE).
2. Rodar `npm run build` no frontend e abrir `npm run preview` para smoke test.
3. Validar script `deploy/deploy_beta_vm.sh` em uma VM de stage.
4. Revisar `.env.beta` com IP/porta corretos.
5. Garantir credenciais de acesso à VM do cliente e permissão para ajustar firewall.

## Bloco B — Na fábrica (VM/PC + Máquina CNC)
1. Ligar a VM/PC e garantir conectividade com a rede da CNC.
2. Acessar `/opt/cnc-telemetry-main` (ou caminho configurado) e confirmar versão atual (`git status`).
3. Verificar serviço: `sudo systemctl status cnc-telemetry`.
4. Se não estiver ativo, aplicar `deploy/deploy_beta_vm.sh` ou `sudo systemctl restart cnc-telemetry`.
5. Testar API local: `curl http://127.0.0.1:8000/healthz`.
6. Ajustar MTConnect/máquina CNC para apontar para o IP da VM.
7. Abrir o painel: `https://<IP-VM>/` (aceitar certificado self-signed se necessário).
8. Validar com o operador que os cartões se movem quando a máquina entra em ciclo.

## Rollback simples
1. Parar serviço: `sudo systemctl stop cnc-telemetry`.
2. Fazer backup do SQLite: `cp backend/telemetry_beta.db backend/telemetry_beta.db.bak`.
3. Restaurar versão anterior do repositório se necessário (`git checkout <tag>`).
4. Reverter configurações da máquina CNC para o estado anterior.

## Referências rápidas
- Deploy backend/infra: `docs/DEPLOY_BETA_VM.md`
- Deploy frontend: `docs/FRONTEND_DEPLOY_VM.md`
- Troubleshooting: `docs/TROUBLESHOOTING_BETA.md`
- Script/systemd: `deploy/deploy_beta_vm.sh`, `deploy/cnc-telemetry.service.example`
