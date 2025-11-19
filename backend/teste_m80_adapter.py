"""Quick manual test for the M80Adapter simulation loop."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import MACHINE_ID, USE_SIMULATION_DATA
from backend.app.services.m80_adapter import M80Adapter


def main() -> None:
    adapter = M80Adapter()
    print(f"USE_SIMULATION_DATA={USE_SIMULATION_DATA}, MACHINE_ID={MACHINE_ID}")

    for idx in range(30):
        payload = adapter.read_telemetry()
        print(f"[{idx:02d}] {payload}")
        time.sleep(1.0)


if __name__ == "__main__":
    main()
