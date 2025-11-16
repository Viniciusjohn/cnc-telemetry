# CNC Telemetry — Troubleshooting Beta

Checklist rápido para diagnosticar problemas em campo durante o piloto.

## 1. Verificar se a API está de pé
```bash
curl http://127.0.0.1:8000/healthz
```
Resposta esperada:
```json
{ "status": "ok", "service": "cnc-telemetry", "version": "v0.3" }
```

## 2. Validar endpoints principais
```bash
curl http://127.0.0.1:8000/v1/machines/SIM_M80_01/status | jq
curl http://127.0.0.1:8000/v1/machines/SIM_M80_01/events | jq
```

Se estiver usando a máquina real, troque `SIM_M80_01` pelo ID configurado.

## 3. Checar serviço/systemd
```bash
sudo systemctl status cnc-telemetry
sudo journalctl -u cnc-telemetry --since "5 minutes ago"
```

- Logs relevantes aparecem com timestamp/nível devido ao `logging.basicConfig` em `backend/main.py`.
- Falhas de banco ausente/SQLite bloqueado aparecerão como WARN/INFO.

## 4. Verificar portas e rede
```bash
sudo ss -tulpn | grep 8000
sudo ufw status verbose
```

- Porta `8000/TCP` deve estar LISTEN.
- Garanta que apenas o IP da máquina CNC/cliente tenha permissão.

## 5. Diagnóstico rápido
1. Serviço ativo (`systemctl status`).
2. Porta ouvindo (`ss -tulpn`).
3. Firewall liberando (`ufw status`).
4. `curl /healthz` responde 200.
5. Logs não mostram exceções recorrentes (`journalctl -u cnc-telemetry`).

Se qualquer etapa falhar:
- Reinicie o serviço: `sudo systemctl restart cnc-telemetry`.
- Reaplique variáveis `.env` e reinicie.
- Revise permissões de arquivo do SQLite (`telemetry_beta.db`).

## 6. Referências
- Deploy backend/infra: `docs/DEPLOY_BETA_VM.md`
- Scripts/systemd: será detalhado em `docs/OPERACAO_BETA_CAMPO.md`
- Seed de dados: `python -m backend.scripts.seed_beta_demo`
