# Guia de Setup Windows – CNC-Genius Telemetria

## 1. Diagnóstico Atual do Ambiente
- **Python detectado**: `Python 3.13.9` (`python --version`).
- **Launcher `py`**: não disponível (`py --list` falhou).
- **Problema principal**: `pip install -r requirements.txt` tenta compilar `pydantic-core` porque ainda não existem wheels oficiais para Python 3.13+. Isso exige Rust/Cargo local.
- **Observação nos requisitos**: adicionamos um comentário em `backend/requirements.txt` informando que `pydantic==2.5.0` só possui wheels até Python 3.12 e que versões mais novas dependem de Rust ([ASSUNCAO]).

## 2. Estratégia Recomendada
1. **Opção A (Recomendada)**: Instalar Python 3.11.x (ou 3.12.x) especificamente para este projeto. Essas versões têm wheels prontos para `pydantic-core`, evitando a dependência de Rust.
2. **Opção B**: Permanecer em Python 3.13+ e instalar o toolchain Rust+Cargo. Funciona, mas demora mais e pode falhar em máquinas sem permissões administrativas.

> ⚠️ **Recomendação**: siga a Opção A. Vamos manter o Python 3.13 instalado para outros usos, mas criar um ambiente virtual com Python 3.11 dedicado ao backend.

## 3. Passo a Passo – Backend

### PASSO 1 – Instalar Python 3.11.x
[ASSUNCAO] Baixe do site oficial (<https://www.python.org/downloads/windows/>) ou use o comando abaixo (PowerShell/Windows Terminal):
```powershell
winget install -e --id Python.Python.3.11
```
Durante a instalação marque **“Add Python to PATH”**.

### PASSO 2 – Criar ambiente virtual
Abra um terminal na pasta do backend e crie o venv usando o Python 3.11 recém-instalado.
```powershell
cd C:\cnc-telemetry-main\backend
"C:\Program Files\Python311\python.exe" -m venv .venv
```
> Ajuste o caminho caso o instalador salve em outro diretório (ex.: `%LocalAppData%\Programs\Python\Python311`).

### PASSO 3 – Ativar o venv
```powershell
C:\cnc-telemetry-main\backend\.venv\Scripts\activate
```
O prompt deve mostrar `(.venv)` no início.

### PASSO 4 – Atualizar pip e instalar dependências
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
Se você instalou Python 3.11, a instalação deve terminar sem compilar nada.

### PASSO 5 – (Opcional) Caso continue em Python 3.13+
Se decidir manter o Python mais novo, instale Rust/Cargo antes de rodar `pip install`:
```powershell
winget install -e --id Rustlang.Rustup
rustup default stable-x86_64-pc-windows-msvc
python -m pip install -r requirements.txt
```
> Esta etapa pode demorar e requer ~1.5 GB livres.

### PASSO 6 – Subir o backend
Com o venv ativo:
```powershell
uvicorn main:app --reload --port 8001
```
O backend ficará disponível em <http://localhost:8001>.

## 4. Passo a Passo – Frontend
Abra outro terminal (fora do venv) e execute:
```powershell
cd C:\cnc-telemetry-main\frontend
npm install
npm run dev
```
A aplicação Vite normalmente sobe em <http://localhost:5173>. Ajuste `VITE_API_BASE` para `http://localhost:8001` se necessário.

## 5. Troubleshooting rápido
| Sintoma | Ação sugerida |
| --- | --- |
| `python` aponta para 3.13 mesmo dentro do projeto | Use o caminho completo para o Python 3.11 ao criar o venv e sempre ative o `.venv`. |
| `pip install` reclama de `pydantic-core` | Confirme que o venv está usando Python 3.11/3.12 ou instale Rust/Cargo e repita a instalação. |
| `uvicorn` não encontrado | Verifique se o `.venv` está ativo; caso contrário, reative e rode `pip install`. |
| `py` comando não existe | Siga os comandos usando `python.exe` diretamente (como nos exemplos acima). |

## 6. Resumo rápido para rodar tudo
1. Instale Python 3.11 (`winget install -e --id Python.Python.3.11`).
2. Crie e ative o venv em `backend/` usando esse Python.
3. `python -m pip install -r requirements.txt`.
4. `uvicorn main:app --reload --port 8001`.
5. No frontend: `npm install && npm run dev`.

Seguindo esses passos, o backend roda em `http://localhost:8001` e o frontend em `http://localhost:5173`, consumindo o contract v0.2 com o log de eventos.
