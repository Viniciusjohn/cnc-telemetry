"""Unified adapter for Mitsubishi M80 telemetry (real or simulated)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from backend.app.config import MACHINE_ID, MACHINE_IP, USE_SIMULATION_DATA

StateType = Literal["running", "stopped", "idle"]


@dataclass
class CNCSimulatorState:
    """Simple structure describing a simulator snapshot."""

    machine_id: str
    rpm: float
    feed_mm_min: float
    state: StateType
    spindle_load_pct: float
    alarm_code: str | None


class CNCSimulatorLogic:
    """Simulação de ~30 minutos com fases fixas."""

    def __init__(self, machine_id: str) -> None:
        self.machine_id = machine_id
        self._tick = 0

    def _build_snapshot(self, state: StateType) -> CNCSimulatorState:
        if state == "running":
            rpm = 3500.0
            feed = 1200.0
            spindle_load = 65.0
        elif state == "stopped":
            rpm = 0.0
            feed = 0.0
            spindle_load = 0.0
        else:  # idle
            rpm = 0.0
            feed = 0.0
            spindle_load = 10.0

        alarm_code = "105" if state == "stopped" else None

        return CNCSimulatorState(
            machine_id=self.machine_id,
            rpm=rpm,
            feed_mm_min=feed,
            state=state,
            spindle_load_pct=spindle_load,
            alarm_code=alarm_code,
        )

    def simulate(self) -> dict:
        self._tick += 1

        if self._tick < 10:
            state: StateType = "idle"
        elif self._tick < 200:
            state = "running"
        elif self._tick < 220:
            state = "stopped"
        else:
            state = "idle"
            if self._tick > 300:
                self._tick = 0

        snapshot = self._build_snapshot(state)

        return {
            "machine_id": snapshot.machine_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rpm": snapshot.rpm,
            "feed_mm_min": snapshot.feed_mm_min,
            "state": snapshot.state,
            "spindle_load_pct": snapshot.spindle_load_pct,
            "alarm_code": snapshot.alarm_code,
        }


class M80Adapter:
    """Fonte única de telemetria M80 (simulada ou real)."""

    def __init__(self) -> None:
        self._machine_id = MACHINE_ID
        self._machine_ip = MACHINE_IP
        self._use_simulation = USE_SIMULATION_DATA
        self._sim = CNCSimulatorLogic(machine_id=self._machine_id) if self._use_simulation else None

    def _read_real_snapshot(self) -> dict:
        # TODO: implementar integração real com a M80 usando MACHINE_IP
        return {
            "machine_id": self._machine_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rpm": 0.0,
            "feed_mm_min": 0.0,
            "state": "idle",
            "spindle_load_pct": 0.0,
            "alarm_code": None,
        }

    def _get_extra_status_data(self, snapshot: dict) -> dict:
        return {
            "spindle_load_pct": snapshot.get("spindle_load_pct", 0.0),
            "alarm_code": snapshot.get("alarm_code"),
        }

    def read_telemetry(self) -> dict:
        if self._use_simulation and self._sim is not None:
            snapshot = self._sim.simulate()
        else:
            snapshot = self._read_real_snapshot()

        ingest = {
            "machine_id": snapshot["machine_id"],
            "timestamp": snapshot["timestamp"],
            "rpm": snapshot["rpm"],
            "feed_mm_min": snapshot["feed_mm_min"],
            "state": snapshot["state"],
        }

        extra = self._get_extra_status_data(snapshot)

        return {
            "ingest": ingest,
            "extra": extra,
        }
