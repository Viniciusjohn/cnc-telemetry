# backend/app/services/oee.py
# OEE Calculation Service
# OEE = Availability × Performance × Quality

from datetime import datetime, time, timedelta, timezone
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

import logging

logger = logging.getLogger(__name__)

try:
    from backend.app.config import TELEMETRY_POLL_INTERVAL_SEC
except Exception:  # pragma: no cover - config import fallback for scripts
    TELEMETRY_POLL_INTERVAL_SEC = 1

SAMPLE_INTERVAL_SEC = max(float(TELEMETRY_POLL_INTERVAL_SEC or 1), 0.1)


def get_shift_times(shift: str, date: datetime.date) -> tuple:
    """
    Get start and end times for a shift.
    
    Shifts:
    - morning: 06:00-14:00
    - afternoon: 14:00-22:00
    - night: 22:00-06:00 (next day)
    """
    if shift == "morning":
        start = datetime.combine(date, time(6, 0)).replace(tzinfo=timezone.utc)
        end = datetime.combine(date, time(14, 0)).replace(tzinfo=timezone.utc)
    elif shift == "afternoon":
        start = datetime.combine(date, time(14, 0)).replace(tzinfo=timezone.utc)
        end = datetime.combine(date, time(22, 0)).replace(tzinfo=timezone.utc)
    elif shift == "night":
        start = datetime.combine(date, time(22, 0)).replace(tzinfo=timezone.utc)
        end = datetime.combine(date + timedelta(days=1), time(6, 0)).replace(tzinfo=timezone.utc)
    else:
        raise ValueError(f"Invalid shift: {shift}")
    
    return start, end


def _empty_shift_oee(machine_id: str, date: str, shift: str, shift_start, shift_end) -> Dict:
    planned_time_min = round((shift_end - shift_start).total_seconds() / 60, 2)
    return {
        "date": date,
        "machine_id": machine_id,
        "shift": shift,
        "shift_start": shift_start.isoformat(),
        "shift_end": shift_end.isoformat(),
        "planned_time_min": planned_time_min,
        "operating_time_min": 0.0,
        "availability": 0.0,
        "performance": 0.0,
        "quality": 0.0,
        "oee": 0.0,
        "samples": {
            "total": 0,
            "running": 0,
            "avg_rpm": 0,
            "max_rpm": 0
        }
    }


def calculate_oee(
    db: Session,
    machine_id: str,
    date: str,  # YYYY-MM-DD
    shift: str = "daily"
) -> Dict:
    """
    Calculate OEE for a machine on a specific date and shift.
    
    Args:
        db: Database session
        machine_id: Machine identifier
        date: Date in YYYY-MM-DD format
        shift: morning, afternoon, night, or daily
    
    Returns:
        Dictionary with OEE metrics
    """
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    
    if shift == "daily":
        shift_start = datetime.combine(date_obj, time(0, 0)).replace(tzinfo=timezone.utc)
        shift_end = shift_start + timedelta(days=1)
        return _calculate_oee_for_window(db, machine_id, date, "daily", shift_start, shift_end)

    # Single shift calculation
    shift_start, shift_end = get_shift_times(shift, date_obj)
    return _calculate_oee_for_window(db, machine_id, date, shift, shift_start, shift_end)


def _calculate_oee_for_window(
    db: Session,
    machine_id: str,
    date: str,
    shift: str,
    shift_start: datetime,
    shift_end: datetime,
) -> Dict:
    """Shared logic for computing OEE in a given window."""

    # Query telemetry samples for this window
    query = text("""
        SELECT 
            COUNT(*) AS total_samples,
            SUM(CASE WHEN state = 'running' THEN 1 ELSE 0 END) AS running_samples,
            AVG(CASE WHEN state = 'running' THEN rpm ELSE NULL END) AS avg_rpm,
            MAX(rpm) AS max_rpm
        FROM telemetry
        WHERE machine_id = :machine_id
          AND ts >= :start_ts
          AND ts < :end_ts
    """)
    
    try:
        result = db.execute(query, {
            "machine_id": machine_id,
            "start_ts": shift_start,
            "end_ts": shift_end
        }).fetchone()
    except (OperationalError, ProgrammingError) as exc:
        logger.info(
            "oee query skipped due to missing table/schema",
            extra={"machine_id": machine_id, "shift": shift, "error": str(exc)}
        )
        return _empty_shift_oee(machine_id, date, shift, shift_start, shift_end)
    
    total_samples = result.total_samples or 0 if result else 0
    running_samples = result.running_samples or 0 if result else 0
    avg_rpm = result.avg_rpm or 0 if result else 0
    max_rpm = result.max_rpm or 0 if result else 0

    # Calculate metrics
    planned_time_min = (shift_end - shift_start).total_seconds() / 60

    operating_time_min = (running_samples * SAMPLE_INTERVAL_SEC) / 60 if running_samples > 0 else 0

    # Availability = Operating Time / Planned Time
    availability = operating_time_min / planned_time_min if planned_time_min > 0 else 0

    # Performance (simplified: actual RPM / programmed RPM)
    # For PMV, we assume 100% performance (need CAM data for real calculation)
    programmed_rpm = 4500  # TODO: Get from CAM/G-code
    performance = 0.0
    if programmed_rpm > 0 and avg_rpm > 0:
        performance = min(avg_rpm / programmed_rpm, 1.0)

    # Quality (simplified: assume 100% good parts for PMV)
    # TODO: Integrate with inspection/QC system
    quality = 0.0 if total_samples == 0 else 1.0

    # OEE = A × P × Q
    oee = availability * performance * quality
    
    if total_samples == 0:
        return _empty_shift_oee(machine_id, date, shift, shift_start, shift_end)

    return {
        "date": date,
        "machine_id": machine_id,
        "shift": shift,
        "shift_start": shift_start.isoformat(),
        "shift_end": shift_end.isoformat(),
        "planned_time_min": round(planned_time_min, 2),
        "operating_time_min": round(operating_time_min, 2),
        "availability": round(availability, 4),
        "performance": round(performance, 4),
        "quality": round(quality, 4),
        "oee": round(oee, 4),
        "samples": {
            "total": total_samples,
            "running": running_samples,
            "avg_rpm": round(avg_rpm, 1) if avg_rpm else 0,
            "max_rpm": round(max_rpm, 1) if max_rpm else 0
        }
    }


def calculate_oee_trend(
    db: Session,
    machine_id: str,
    from_date: str,
    to_date: str,
    shift: str = "daily"
) -> List[Dict]:
    """
    Calculate OEE trend over a date range.
    
    Args:
        db: Database session
        machine_id: Machine identifier
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        shift: morning, afternoon, night, or daily
    
    Returns:
        List of OEE calculations per date
    """
    from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
    to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
    
    trend = []
    current = from_dt
    
    while current <= to_dt:
        oee_data = calculate_oee(db, machine_id, current.strftime("%Y-%m-%d"), shift)
        trend.append(oee_data)
        current += timedelta(days=1)
    
    return trend


def get_oee_benchmark(oee: float) -> Dict:
    """
    Classify OEE against industry benchmarks.
    
    Benchmarks:
    - < 60%: Unacceptable
    - 60-70%: Fair
    - 70-85%: Competitive
    - > 85%: World Class
    """
    if oee < 0.60:
        return {
            "classification": "unacceptable",
            "label": "❌ Inaceitável",
            "color": "#ef4444",
            "target": 0.70
        }
    elif oee < 0.70:
        return {
            "classification": "fair",
            "label": "⚠️ Razoável",
            "color": "#f59e0b",
            "target": 0.75
        }
    elif oee < 0.85:
        return {
            "classification": "competitive",
            "label": "✅ Competitivo",
            "color": "#10b981",
            "target": 0.85
        }
    else:
        return {
            "classification": "world_class",
            "label": "🏆 World Class",
            "color": "#3b82f6",
            "target": 0.90
        }
