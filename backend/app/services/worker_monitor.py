from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Estado em memória do worker M80
_worker_enabled: bool = False
_worker_last_snapshot_ts: Optional[datetime] = None
_worker_consecutive_errors: int = 0


def mark_worker_enabled(enabled: bool) -> None:
    global _worker_enabled
    _worker_enabled = bool(enabled)


def mark_snapshot_success(ts: Optional[datetime] = None) -> None:
    """Chamar sempre que um snapshot M80 for processado com sucesso."""
    global _worker_last_snapshot_ts, _worker_consecutive_errors

    _worker_consecutive_errors = 0
    _worker_last_snapshot_ts = ts or datetime.now(timezone.utc)


def mark_snapshot_error() -> None:
    """Chamar dentro do except do loop do worker."""
    global _worker_consecutive_errors
    _worker_consecutive_errors += 1


def get_worker_status() -> Dict[str, Any]:
    """Retorna um dicionário serializável para ser incluído no /healthz."""
    if _worker_last_snapshot_ts is None:
        last_ts: Optional[str] = None
    else:
        last_ts = _worker_last_snapshot_ts.isoformat()

    return {
        "worker_m80_enabled": _worker_enabled,
        "worker_m80_last_snapshot_ts": last_ts,
        "worker_m80_consecutive_errors": _worker_consecutive_errors,
    }
