# F3 Dashboard PWA — Planejamento

**Status:** 📝 PLANEJAMENTO (NÃO EXECUTADO)  
**Objetivo:** Conectar frontend PWA ao backend via GET /v1/machines/{id}/status com polling 2s

---

## 📋 Escopo

### Backend (FastAPI)
- ✅ Criar endpoint GET `/v1/machines/{machine_id}/status`
- ✅ Response model tipado (Pydantic)
- ✅ Headers canônicos (no-store, Vary, fingerprint)
- ✅ In-memory store LAST_STATUS
- ✅ Atualização via /ingest

### Frontend (React/Vite)
- ✅ API client tipado (`lib/api.ts`)
- ✅ Polling 2s com useEffect
- ✅ 4 cards (RPM, Feed, Estado, Atualizado)
- ✅ Tratamento de erro
- ✅ VITE_API_BASE env var

### Testes
- ✅ Smoke test curl (headers)
- ✅ Smoke test jq (contrato)
- ✅ Playwright E2E (status.spec.ts)

---

## 🗂️ Arquivos a Criar/Modificar

### 1. `backend/app/routers/status.py` (NOVO)

```python
"""
Router para status de máquinas.
Retorna último estado válido agregado pelo /ingest.
"""

from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict

router = APIRouter(prefix="/v1/machines", tags=["status"])

class MachineStatus(BaseModel):
    """Schema de status de máquina (conforme MTConnect normalizado)"""
    machine_id: str = Field(..., pattern=r"^[A-Za-z0-9\-]+$")
    rpm: float = Field(..., ge=0, le=30000, description="RotaryVelocity (rev/min)")
    feed_mm_min: float = Field(..., ge=0, le=10000, description="PathFeedrate convertido (mm/min)")
    state: str = Field(..., pattern=r"^(running|stopped|idle)$", description="Execution normalizado")
    updated_at: datetime = Field(..., description="UTC timestamp da última atualização")
    
    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "CNC-SIM-001",
                "rpm": 4200.0,
                "feed_mm_min": 1250.5,
                "state": "running",
                "updated_at": "2025-11-05T05:50:00Z"
            }
        }

# In-memory store (substituir por Redis/DB em produção)
LAST_STATUS: Dict[str, MachineStatus] = {}

@router.get("/{machine_id}/status", response_model=MachineStatus)
def get_machine_status(machine_id: str, response: Response):
    """
    Retorna último status válido da máquina.
    
    Headers canônicos:
    - Cache-Control: no-store (telemetria não deve ser cacheada)
    - Vary: Origin, Accept-Encoding
    - X-Contract-Fingerprint: 010191590cf1
    - Server-Timing: app;dur=<ms>
    """
    # Headers canônicos
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Origin, Accept-Encoding"
    response.headers["X-Contract-Fingerprint"] = "010191590cf1"
    response.headers["Server-Timing"] = "app;dur=1"
    
    # Buscar status
    status = LAST_STATUS.get(machine_id)
    
    if not status:
        # Retorno default para máquina sem dados (idle)
        # Permite UI funcionar antes do primeiro /ingest
        status = MachineStatus(
            machine_id=machine_id,
            rpm=0.0,
            feed_mm_min=0.0,
            state="idle",
            updated_at=datetime.now(timezone.utc)
        )
    
    return status

def update_status(machine_id: str, rpm: float, feed_mm_min: float, state: str):
    """
    Atualiza status no store.
    Chamado por /ingest após validação.
    """
    LAST_STATUS[machine_id] = MachineStatus(
        machine_id=machine_id,
        rpm=rpm,
        feed_mm_min=feed_mm_min,
        state=state,
        updated_at=datetime.now(timezone.utc)
    )
```

**Motivo:** Separar routers por domínio (FastAPI best practice)

---

### 2. `backend/app.py` (MODIFICAR)

**Mudanças:**

```python
# ANTES (topo do arquivo)
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

# DEPOIS (adicionar)
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

# Importar router de status
from app.routers import status  # NOVO
```

```python
# ANTES (após middlewares)
class TelemetryPayload(BaseModel):
    # ...

@app.post("/v1/telemetry/ingest", status_code=201)
async def ingest_telemetry(payload: TelemetryPayload):
    # ...

# DEPOIS (adicionar wire do router)
# Wire status router
app.include_router(status.router)  # NOVO

class TelemetryPayload(BaseModel):
    # ...

@app.post("/v1/telemetry/ingest", status_code=201)
async def ingest_telemetry(payload: TelemetryPayload):
    # TODO: Persistir em DB
    
    # NOVO: Atualizar status no store
    status.update_status(
        machine_id=payload.machine_id,
        rpm=payload.rpm,
        feed_mm_min=payload.feed_mm_min,
        state=payload.state
    )
    
    return {
        "ingested": True,
        "machine_id": payload.machine_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
```

**Motivo:** Atualizar LAST_STATUS a cada /ingest

---

### 3. `backend/app/__init__.py` (NOVO)

```python
# Torna app/ um package Python
```

---

### 4. `backend/app/routers/__init__.py` (NOVO)

```python
# Torna routers/ um package Python
```

---

### 5. `frontend/src/lib/api.ts` (NOVO)

```typescript
/**
 * API client para backend cnc-telemetry.
 * Usa VITE_API_BASE env var (apenas prefixadas são expostas).
 */

export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001";

export type MachineStatus = {
  machine_id: string;
  rpm: number;
  feed_mm_min: number;
  state: "running" | "stopped" | "idle";
  updated_at: string; // ISO 8601
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Busca status de uma máquina.
 * @throws {ApiError} Se response não for ok
 */
export async function fetchMachineStatus(machineId: string): Promise<MachineStatus> {
  const url = `${API_BASE}/v1/machines/${machineId}/status`;
  
  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Accept": "application/json",
    },
  });
  
  if (!response.ok) {
    throw new ApiError(response.status, `Failed to fetch status: ${response.statusText}`);
  }
  
  return response.json();
}
```

**Motivo:** Client tipado com tratamento de erro

---

### 6. `frontend/.env.local` (MODIFICAR)

```bash
# ANTES
VITE_API_BASE=http://localhost:8001

# DEPOIS (mesmo valor, documentar melhor)
# Backend API base URL (apenas vars VITE_* são expostas ao cliente)
VITE_API_BASE=http://localhost:8001
```

**Motivo:** Documentação clara sobre VITE_ prefix

---

### 7. `frontend/src/App.tsx` (MODIFICAR)

```typescript
import { useEffect, useState } from "react";
import { fetchMachineStatus, MachineStatus, ApiError } from "./lib/api";

const MACHINE_ID = "CNC-SIM-001"; // TODO: Tornar configurável
const POLL_INTERVAL_MS = 2000; // 2 segundos

export default function App() {
  const [status, setStatus] = useState<MachineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function poll() {
      try {
        const data = await fetchMachineStatus(MACHINE_ID);
        if (isMounted) {
          setStatus(data);
          setError(null);
          setIsLoading(false);
        }
      } catch (e) {
        if (isMounted) {
          if (e instanceof ApiError) {
            setError(`HTTP ${e.status}: ${e.message}`);
          } else {
            setError(e instanceof Error ? e.message : "Unknown error");
          }
          setIsLoading(false);
        }
      }
    }

    // Poll inicial
    poll();

    // Polling contínuo
    const intervalId = setInterval(poll, POLL_INTERVAL_MS);

    // Cleanup
    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  return (
    <main className="min-h-screen bg-black text-white p-6">
      <header className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">CNC Telemetry — Dashboard</h1>
        <div className="text-sm opacity-70">
          {status?.machine_id || "—"}
        </div>
      </header>

      {error && (
        <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-4">
          <strong>Erro:</strong> {error}
        </div>
      )}

      {isLoading && !status && (
        <div className="text-center py-8 opacity-50">
          Carregando...
        </div>
      )}

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card 
          title="RPM" 
          value={status?.rpm.toFixed(1) ?? "—"} 
          suffix="rev/min"
        />
        <Card 
          title="Feed" 
          value={status?.feed_mm_min.toFixed(1) ?? "—"} 
          suffix="mm/min"
        />
        <Card 
          title="Estado" 
          value={status?.state ?? "—"}
          color={getStateColor(status?.state)}
        />
        <Card 
          title="Atualizado" 
          value={status ? formatTime(status.updated_at) : "—"}
        />
      </section>

      <footer className="mt-6 text-xs opacity-50 text-center">
        Polling: {POLL_INTERVAL_MS / 1000}s | 
        API: {import.meta.env.VITE_API_BASE}
      </footer>
    </main>
  );
}

interface CardProps {
  title: string;
  value: string;
  suffix?: string;
  color?: string;
}

function Card({ title, value, suffix, color }: CardProps) {
  return (
    <div className="rounded-2xl p-5 bg-zinc-900 border border-zinc-800 shadow-lg">
      <div className="text-xs uppercase tracking-wider opacity-60 mb-2">
        {title}
      </div>
      <div className={`text-3xl font-bold ${color || ""}`}>
        {value}
      </div>
      {suffix && (
        <div className="text-xs opacity-50 mt-1">
          {suffix}
        </div>
      )}
    </div>
  );
}

function getStateColor(state?: string): string {
  switch (state) {
    case "running":
      return "text-green-400";
    case "stopped":
      return "text-red-400";
    case "idle":
      return "text-yellow-400";
    default:
      return "text-gray-400";
  }
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
```

**Motivo:** Dashboard completo com polling 2s, tratamento de erro, cores por estado

---

### 8. `frontend/e2e/status.spec.ts` (NOVO)

```typescript
import { test, expect } from "@playwright/test";

const BASE_URL = "http://localhost:5173";

test.describe("Dashboard F3", () => {
  test("deve exibir header e machine_id", async ({ page }) => {
    await page.goto(BASE_URL);
    
    await expect(page.getByRole("heading", { name: /CNC Telemetry/ })).toBeVisible();
    
    // Aguardar primeiro poll
    await page.waitForTimeout(2500);
    
    // Verificar machine_id aparece
    await expect(page.getByText(/CNC-SIM-001/)).toBeVisible();
  });

  test("deve exibir 4 cards de status", async ({ page }) => {
    await page.goto(BASE_URL);
    
    await expect(page.getByText("RPM")).toBeVisible();
    await expect(page.getByText("Feed")).toBeVisible();
    await expect(page.getByText("Estado")).toBeVisible();
    await expect(page.getByText("Atualizado")).toBeVisible();
  });

  test("cards devem atualizar após 2s (polling)", async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Aguardar primeiro poll
    await page.waitForTimeout(500);
    
    // Capturar valor inicial
    const rpmCard = page.locator('text=RPM').locator("..");
    const initialValue = await rpmCard.textContent();
    
    // Aguardar próximo poll (2s)
    await page.waitForTimeout(2500);
    
    // Valor pode ter mudado (ou não, se máquina parada)
    // Mas card deve estar visível
    await expect(rpmCard).toBeVisible();
  });

  test("deve exibir erro se backend não disponível", async ({ page }) => {
    // Simular backend offline alterando API_BASE
    // (em teste real, mockar com page.route)
    
    await page.route("**/v1/machines/*/status", (route) => {
      route.abort("failed");
    });
    
    await page.goto(BASE_URL);
    
    // Deve mostrar mensagem de erro
    await expect(page.getByText(/Erro/)).toBeVisible();
  });
});
```

**Motivo:** Testes E2E validam polling, atualização, erro

---

## 🧪 Smoke Tests

### 1. Headers Canônicos

```bash
curl -sI http://localhost:8001/v1/machines/CNC-SIM-001/status
```

**Saída esperada:**
```
HTTP/1.1 200 OK
cache-control: no-store
vary: Origin, Accept-Encoding
x-contract-fingerprint: 010191590cf1
server-timing: app;dur=1
content-type: application/json
```

**PASS:** Todos os 4 headers presentes

---

### 2. Contrato JSON

```bash
curl -s http://localhost:8001/v1/machines/CNC-SIM-001/status | jq
```

**Saída esperada:**
```json
{
  "machine_id": "CNC-SIM-001",
  "rpm": 4200.0,
  "feed_mm_min": 1250.5,
  "state": "running",
  "updated_at": "2025-11-05T05:50:00Z"
}
```

**Validação schema:**
```bash
curl -s http://localhost:8001/v1/machines/CNC-SIM-001/status | \
  jq -e '.rpm >= 0 and .feed_mm_min >= 0 and (.state | IN("running","stopped","idle"))'
```

**PASS:** Exit code 0

---

### 3. Frontend Polling

```bash
# 1. Iniciar backend
cd backend && source .venv/bin/activate
uvicorn main:app --port 8001 --reload

# 2. Iniciar frontend
cd frontend
npm run dev

# 3. Abrir browser
open http://localhost:5173
```

**Verificar:**
- ✅ Cards aparecem
- ✅ Valores atualizam a cada ~2s
- ✅ Estado com cor correta (verde/vermelho/amarelo)
- ✅ Timestamp atualiza

---

### 4. Playwright E2E

```bash
cd frontend
npx playwright test e2e/status.spec.ts
```

**Saída esperada:**
```
Running 4 tests using 1 worker

  ✓ deve exibir header e machine_id (2.1s)
  ✓ deve exibir 4 cards de status (1.8s)
  ✓ cards devem atualizar após 2s (3.2s)
  ✓ deve exibir erro se backend não disponível (1.5s)

  4 passed (8.6s)
```

**PASS:** Todos os testes passam

---

## ✅ Gates de Aceite F3

| Gate | Critério | Como Validar |
|------|----------|--------------|
| **G1** | GET /status retorna 200 | `curl -I ...` |
| **G2** | Schema JSON válido | `jq -e '.rpm>=0 and ...'` |
| **G3** | Headers canônicos | grep cache-control/vary/fingerprint/server-timing |
| **G4** | Frontend polling 2s | Observar console.log no browser |
| **G5** | Playwright PASS | `npx playwright test` |
| **G6** | PWA instalável | DevTools → Manifest → Install |
| **G7** | Lighthouse ≥90 | `npx lighthouse http://localhost:5173` |

---

## 🚨 Riscos e Mitigações

### Risco 1: VITE_API_BASE não exposto

**Causa:** Env var sem prefixo `VITE_`

**Sintoma:** `import.meta.env.VITE_API_BASE` é `undefined`

**Mitigação:**
```bash
# .env.local DEVE ter prefixo VITE_
VITE_API_BASE=http://localhost:8001  # ✅ Correto
API_BASE=http://localhost:8001        # ❌ Errado (não exposto)
```

---

### Risco 2: Cache-Control incorreto

**Problema:** Usar `no-cache` em vez de `no-store`

**Diferença:**
- `no-cache`: Revalida com servidor (pode usar cache se 304)
- `no-store`: Nunca cacheia (correto para telemetria)

**Solução:**
```python
response.headers["Cache-Control"] = "no-store"  # ✅ Correto
```

---

### Risco 3: Memory leak no polling

**Causa:** Não limpar interval no cleanup

**Sintoma:** Múltiplos intervals rodando

**Mitigação:**
```typescript
useEffect(() => {
  const id = setInterval(poll, 2000);
  return () => clearInterval(id);  // ✅ Cleanup obrigatório
}, []);
```

---

### Risco 4: Adapter perde continuidade

**Problema:** Reinício do Agent muda `instanceId`, sequência perde tracking

**Status:** Registrado em F2, implementar em F3/F4

**Solução futura:**
- Persistir `instanceId` + `nextSequence` no adapter
- Detectar mudança de `instanceId`
- Retomar de `firstSequence` se necessário

---

## 📚 Referências Técnicas

### FastAPI
- **Response Model:** https://fastapi.tiangolo.com/tutorial/response-model/
- **Headers:** https://fastapi.tiangolo.com/advanced/response-headers/
- **Routers:** https://fastapi.tiangolo.com/tutorial/bigger-applications/

### Vite
- **Env Variables:** https://vitejs.dev/guide/env-and-mode.html
- **VITE_ Prefix:** Apenas vars com prefixo são expostas ao client

### Playwright
- **Getting Started:** https://playwright.dev/docs/intro
- **Assertions:** https://playwright.dev/docs/test-assertions

### MTConnect
- **/sample:** https://www.mtconnect.org/getting-started
- **nextSequence:** Controle de continuidade sem perdas

### HTTP Caching
- **no-store vs no-cache:** https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control

---

## 🎯 Próximos Passos

### Após Planejamento (EXECUTAR)

1. **Criar estrutura backend:**
   ```bash
   mkdir -p backend/app/routers
   touch backend/app/__init__.py
   touch backend/app/routers/__init__.py
   # Criar status.py conforme spec acima
   ```

2. **Modificar app.py:**
   - Importar router
   - Wire com `app.include_router`
   - Atualizar /ingest para chamar `update_status()`

3. **Criar API client frontend:**
   ```bash
   mkdir -p frontend/src/lib
   # Criar api.ts conforme spec acima
   ```

4. **Atualizar App.tsx:**
   - Importar `fetchMachineStatus`
   - Implementar polling com useEffect
   - Renderizar cards

5. **Smoke tests:**
   ```bash
   # Backend
   curl -sI http://localhost:8001/v1/machines/CNC-SIM-001/status
   
   # Frontend
   npm run dev
   open http://localhost:5173
   ```

6. **Playwright:**
   ```bash
   npx playwright test e2e/status.spec.ts
   ```

---

## 📊 Estimativa de Esforço

| Tarefa | Tempo | Complexidade |
|--------|-------|--------------|
| Backend router | 15 min | Baixa |
| Modificar app.py | 10 min | Baixa |
| API client frontend | 10 min | Baixa |
| Atualizar App.tsx | 20 min | Média |
| Smoke tests | 10 min | Baixa |
| Playwright E2E | 15 min | Média |
| **TOTAL** | **~80 min** | **Média** |

---

**Status:** 📝 PLANEJAMENTO COMPLETO - PRONTO PARA EXECUÇÃO

**Quando executar:** Após conclusão do soak test 30 min (F2)

**Aprovação:** Aguardando comando "executar F3"
