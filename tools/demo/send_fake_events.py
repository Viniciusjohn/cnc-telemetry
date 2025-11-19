"""Modo demo para o CNC Telemetry.

Envia eventos artificiais para demonstrar o painel sem conexão com a CNC.
"""
from __future__ import annotations

import argparse
import os
import random
import time
from datetime import datetime, timezone

import httpx

EVENTS = [
    ("IDLE", "DEMO_IDLE"),
    ("RUNNING", "DEMO_RUN_001"),
    ("RUNNING", "DEMO_RUN_002"),
    ("ALARM", "DEMO_ALARM_001"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enviar eventos fake para o CNC Telemetry")
    parser.add_argument(
        "--api-url",
        default=os.getenv("TELEMETRY_BASE_URL", "http://localhost:8001"),
        help="URL base do backend (default: $TELEMETRY_BASE_URL ou http://localhost:8001)",
    )
    parser.add_argument(
        "--machine-id",
        default=os.getenv("TELEMETRY_MACHINE_ID", "DEMO-MACHINE"),
        help="Identificador da máquina (apenas letras, números e hífen)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2,
        help="Intervalo em segundos entre eventos",
    )
    parser.add_argument(
        "--burst",
        type=int,
        default=0,
        help="Número de eventos a enviar (0 = loop infinito)",
    )
    return parser.parse_args()


def build_payload(machine_id: str, state: str) -> dict:
    return {
        "machine_id": machine_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "rpm": 2000 if state == "RUNNING" else 0,
        "feed_mm_min": 150 if state == "RUNNING" else 0,
        "state": "running" if state == "RUNNING" else ("idle" if state == "IDLE" else "stopped"),
    }


def send_payload(base_url: str, payload: dict, state: str, program: str) -> None:
    url = f"{base_url.rstrip('/')}/v1/telemetry/ingest"
    with httpx.Client(timeout=5) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
    print(f"[DEMO] {payload['timestamp']} :: {state:<8} ({program}) -> {resp.status_code}")


def main() -> None:
    args = parse_args()
    base_url = args.api_url
    machine_id = args.machine_id

    if "_" in machine_id:
        raise SystemExit("machine_id inválido: use apenas letras, números e hífen (-). Ex: M80-DEMO-01")

    print("=== CNC Telemetry Demo Mode ===")
    print(f"Base URL: {base_url}")
    print(f"Machine ID: {machine_id}")
    print("Ctrl+C para interromper.\n")

    sent = 0
    while True:
        state, program = random.choice(EVENTS)
        payload = build_payload(machine_id, state)
        send_payload(base_url, payload, state, program)
        sent += 1
        if args.burst and sent >= args.burst:
            break
        time.sleep(args.interval)

    print("=== Demo concluída ===")


if __name__ == "__main__":
    main()
