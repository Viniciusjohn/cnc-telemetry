"""Centralized application settings for CNC Telemetry."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key)
    if value is None:
        return default
    return value


@dataclass(frozen=True)
class Settings:
    """Minimal settings object for pilot deployments."""

    database_url: str = _env(
        "TELEMETRY_DATABASE_URL",
        _env("DATABASE_URL", "sqlite:///./telemetry_beta.db"),
    )
    api_host: str = _env("TELEMETRY_API_HOST", "0.0.0.0") or "0.0.0.0"
    api_port: int = int(_env("TELEMETRY_API_PORT", "8000") or 8000)


settings = Settings()
