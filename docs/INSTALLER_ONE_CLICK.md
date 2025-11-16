# CNC Telemetry – Instalador One-Click (.exe)

Este guia explica como gerar e utilizar o instalador em formato `.exe` que encapsula o script `install_cnc_telemetry.ps1`. O objetivo é permitir que o cliente execute apenas um arquivo e tenha todo o ambiente configurado automaticamente.

## 1. Pré-requisitos da máquina de build

1. Windows 10 ou superior com PowerShell 5+ (ou PowerShell 7).
2. Git + repo `cnc-telemetry` já clonado.
3. Acesso à internet para instalar o módulo `ps2exe` na primeira execução.
4. `install_cnc_telemetry.ps1` atualizado na raiz do projeto (já incluso no repo).

## 2. Gerando o instalador

No diretório raiz do projeto:

```powershell
pwsh .\scripts\build_installer.ps1
```

O script:
- Resolve o caminho do `install_cnc_telemetry.ps1`.
- Garante que o módulo `ps2exe` está disponível (instala automaticamente para CurrentUser se permitir).
- Gera `dist\CNC-Telemetry-Installer.exe` (diretório criado se não existir).

### Parâmetros opcionais

| Parâmetro             | Padrão                                         | Descrição                                        |
|-----------------------|------------------------------------------------|--------------------------------------------------|
| `-SourceScript`       | `..\install_cnc_telemetry.ps1`                 | Script PowerShell que será empacotado.           |
| `-OutputExe`          | `..\dist\CNC-Telemetry-Installer.exe`         | Caminho do `.exe` final.                         |
| `-ProductName`        | `CNC Telemetry Installer`                      | Nome exibido nas propriedades do executável.     |
| `-CompanyName`        | `CNC-Genius`                                   | Nome da empresa nas propriedades.                |
| `-ProductVersion`     | `1.0.0`                                        | Versão embutida no arquivo.                      |
| `-SkipModuleInstall`  | (switch desligado)                             | Falha se `ps2exe` não estiver presente.          |

Exemplo alterando saída e versão:

```powershell
pwsh .\scripts\build_installer.ps1 -OutputExe C:\Kit\CNC-Telemetry.exe -ProductVersion 1.1.0
```

## 3. O que o instalador faz

O executável roda o mesmo fluxo do `install_cnc_telemetry.ps1`:
1. Checa dependências (Python, Node, npm, NSSM) e caminhos default.
2. Cria/atualiza `.venv`, instala requirements do backend, e garante `.env.beta`.
3. Executa o seed opcional (`backend/scripts/seed_beta_demo.py`).
4. Instala dependências do frontend e roda `npm run build`.
5. Registra/atualiza o serviço Windows via NSSM para expor o backend em `0.0.0.0:8001`.
6. Faz um health-check `http://localhost:8001/healthz` para confirmar.

## 4. Como usar no cliente

1. Copie `CNC-Telemetry-Installer.exe`, o diretório `frontend/dist/` (se for servir estaticamente) e demais artefatos desejados para o computador alvo.
2. Execute o `.exe` com privilégios de administrador (botão direito → "Executar como administrador").
3. Aguarde as mensagens no console. Ao final, o script informa se o `/healthz` respondeu `200`.
4. Verifique o serviço `CncTelemetryService` em `services.msc` ou com `nssm status CncTelemetryService`.
5. Abra o frontend (build gerado) apontando para `http://<IP_DO_HOST>:8001`.

## 5. Solução de problemas rápida

- **Dependências ausentes**: se Python/Node/npm/NSSM não estiverem no PATH, o instalador aborta informando qual comando falta.
- **Porta 8001 ocupada**: pare serviços anteriores (`netstat -ano | findstr :8001` + `Stop-Process`).
- **Seed falhou**: o instalador não interrompe; rode manualmente `python -m backend.scripts.seed_beta_demo` se precisar.
- **Firewall bloqueando**: abra a porta 8001 para conexões internas/externas, conforme o ambiente do cliente.

Com esse fluxo, basta entregar o `.exe` + build do frontend e instruir o cliente a executá-lo para ter o CNC Telemetry operante em minutos.
