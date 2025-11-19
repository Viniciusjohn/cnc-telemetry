"""Pipeline helpers that connect the M80 adapter to the backend storage."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from backend.app.db import SessionLocal, Telemetry
from backend.app.routers import status as status_router
from backend.app.services.m80_adapter import M80Adapter

logger = logging.getLogger(__name__)

_adapter: Optional[M80Adapter] = None


def _get_adapter() -> M80Adapter:
    global _adapter
    if _adapter is None:
        _adapter = M80Adapter()
    return _adapter


def process_m80_snapshot() -> None:
    """Read a single snapshot from the adapter and persist it."""

    adapter = _get_adapter()
    payload = adapter.read_telemetry()
    ingest: dict[str, Any] = payload["ingest"]
    extra: dict[str, Any] = payload.get("extra", {})

    timestamp = datetime.fromisoformat(ingest["timestamp"].replace("Z", "+00:00"))

    session = SessionLocal()
    try:
        telemetry_row = Telemetry(
            ts=timestamp,
            machine_id=ingest["machine_id"],
            rpm=ingest["rpm"],
            feed_mm_min=ingest["feed_mm_min"],
            state=ingest["state"],
            sequence=None,
            src="m80-adapter",
        )
        session.add(telemetry_row)
        try:
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.info("telemetry insert skipped", extra={"error": str(exc)})

        status_router.update_status(
            machine_id=ingest["machine_id"],
            rpm=ingest["rpm"],
            feed_mm_min=ingest["feed_mm_min"],
            state=ingest["state"],
            db=session,
            extra=extra,
            snapshot_ts=timestamp,
        )
    finally:
        session.close()
