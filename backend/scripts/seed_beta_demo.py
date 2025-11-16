"""Seed helper for CNC Telemetry beta demos.

Creates a handful of telemetry samples and events for SIM_M80_01
so that /status, /events, /history e /oee tenham dados mínimos.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.db import Base, engine, get_db_context, Telemetry, TelemetryEvents

logger = logging.getLogger(__name__)
DEFAULT_MACHINE_ID = "SIM_M80_01"


def seed(machine_id: str = DEFAULT_MACHINE_ID, samples: int = 5) -> None:
    Base.metadata.create_all(bind=engine)

    base_ts = datetime.now(timezone.utc)
    with get_db_context() as db:
        next_id = 1
        for offset in range(samples):
            ts = base_ts - timedelta(minutes=offset)
            telemetry = Telemetry(
                ts=ts,
                machine_id=machine_id,
                rpm=1800 + offset * 10,
                feed_mm_min=250 + offset * 5,
                state="running" if offset % 3 != 0 else "idle",
                sequence=offset,
                src="seed_beta_demo",
            )
            db.merge(telemetry)

            event = TelemetryEvents(
                id=next_id,
                machine_id=machine_id,
                timestamp_utc=ts,
                mode="AUTOMATIC",
                execution="EXECUTING" if offset % 3 != 0 else "READY",
                rpm=telemetry.rpm,
                feed_rate=telemetry.feed_mm_min,
                spindle_load_pct=15.0,
                tool_id=f"T{offset:02d}",
                alarm_code=None,
                alarm_message=None,
                part_count=offset,
                controller_family="MITSUBISHI_M8X",
                source="seed_beta_demo",
            )
            db.add(event)
            next_id += 1

    logger.info(
        "Seed beta demo completed",
        extra={"machine_id": machine_id, "samples": samples},
    )


def main() -> None:
    seed()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
