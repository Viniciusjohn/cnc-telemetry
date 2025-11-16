"""FastAPI entrypoint for CNC Telemetry.

Use `app.config.settings` for host/port/database overrides.
"""

import logging

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Import routers
from backend.app.routers import history, oee, status

# Import DB
from backend.app.db import Telemetry, get_db

APP_VERSION = "v0.3"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("cnc-telemetry")

app = FastAPI(title="CNC Telemetry API", version=APP_VERSION)

# Wire routers
app.include_router(status.router)
app.include_router(history.router)
app.include_router(oee.router)

# CORS
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["Content-Type","X-Request-Id","X-Contract-Fingerprint"],
    expose_headers=["X-Contract-Fingerprint","X-Request-Id","Server-Timing"],
    max_age=600
)

# Enforce preflight 204 (após CORSMiddleware calcular Access-Control-*)
@app.middleware("http")
async def enforce_preflight_204(request: Request, call_next):
    res = await call_next(request)
    # Detecta preflight OPTIONS
    if request.method == "OPTIONS" and request.headers.get("Access-Control-Request-Method"):
        # Copia todos os headers gerados (CORS + canônicos)
        hdrs = {k: v for k, v in res.headers.items()}
        # Remove content-type e content-length para 204
        hdrs.pop("content-type", None)
        hdrs.pop("content-length", None)
        # Retorna 204 sem corpo
        return Response(status_code=204, headers=hdrs, content=b"")
    return res


@app.on_event("startup")
async def log_startup() -> None:
    logger.info("CNC Telemetry API starting", extra={"version": APP_VERSION})


@app.get("/healthz", tags=["infra"])
async def healthz():
    return {
        "status": "ok",
        "service": "cnc-telemetry",
        "version": APP_VERSION,
    }

@app.middleware("http")
async def headers(req, call_next):
    res = await call_next(req)
    res.headers.update({
        "Cache-Control":"no-store",
        "Vary":"Origin, Accept-Encoding",
        "Server-Timing":"app;dur=1",
        "X-Contract-Fingerprint":"010191590cf1"
    })
    return res

class TelemetryPayload(BaseModel):
    machine_id: str = Field(..., pattern=r"^[a-zA-Z0-9-]+$")
    timestamp: str  # ISO 8601
    rpm: float = Field(..., ge=0, le=30000)
    feed_mm_min: float = Field(..., ge=0, le=10000)
    state: Literal["running", "stopped", "idle"]

@app.post("/v1/telemetry/ingest", status_code=201)
async def ingest_telemetry(payload: TelemetryPayload, db: Session = Depends(get_db)):
    """Ingerir dados de telemetria (idempotência: machine_id+timestamp)"""
    
    # Parse timestamp
    ts = datetime.fromisoformat(payload.timestamp.replace('Z', '+00:00'))
    
    # Persistir em TimescaleDB
    try:
        db_record = Telemetry(
            ts=ts,
            machine_id=payload.machine_id,
            rpm=payload.rpm,
            feed_mm_min=payload.feed_mm_min,
            state=payload.state,
            sequence=None  # TODO: extrair do MTConnect se disponível
        )
        db.add(db_record)
        db.commit()
    except Exception as e:
        # Se já existe (duplicate key), apenas atualizar status
        db.rollback()
        print(f"DB insert failed (possibly duplicate): {e}")
    
    # Atualizar status em memória (para /status endpoint) + persistir evento v0.2
    status.update_status(
        machine_id=payload.machine_id,
        rpm=payload.rpm,
        feed_mm_min=payload.feed_mm_min,
        state=payload.state,
        db=db  # [v0.2] Passar sessão DB para persistir histórico
    )
    
    return {
        "ingested": True,
        "machine_id": payload.machine_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }

# Endpoint /v1/machines/{id}/status movido para app/routers/status.py
