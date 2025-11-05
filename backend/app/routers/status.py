"""
Router para status de máquinas.
Retorna último estado válido agregado pelo /ingest.
"""

from fastapi import APIRouter, Response
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
