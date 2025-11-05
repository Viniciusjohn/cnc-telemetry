# backend/app/routers/history.py
# Historical telemetry data API

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Optional, List, Dict

from ..db import get_db

router = APIRouter(prefix="/v1/machines", tags=["history"])


@router.get("/{machine_id}/history")
def get_machine_history(
    machine_id: str,
    from_ts: str = Query(..., description="Start timestamp (ISO 8601)"),
    to_ts: str = Query(..., description="End timestamp (ISO 8601)"),
    resolution: str = Query("5m", description="raw | 5m | 1h | 1d"),
    limit: int = Query(10000, description="Max number of records"),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get historical telemetry data for a machine.
    
    Resolutions:
    - raw: Raw telemetry samples (2-second intervals)
    - 5m: 5-minute aggregates
    - 1h: 1-hour aggregates
    - 1d: 1-day aggregates
    
    Example:
        GET /v1/machines/CNC-SIM-001/history?from_ts=2025-10-05T00:00:00Z&to_ts=2025-11-05T00:00:00Z&resolution=1h
    """
    try:
        # Parse timestamps
        from_dt = datetime.fromisoformat(from_ts.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(to_ts.replace('Z', '+00:00'))
        
        # Validate date range
        if from_dt >= to_dt:
            raise HTTPException(status_code=400, detail="from_ts must be before to_ts")
        
        # Select appropriate table/view based on resolution
        if resolution == "raw":
            query = text("""
                SELECT 
                    ts,
                    machine_id,
                    rpm,
                    feed_mm_min,
                    state,
                    sequence
                FROM telemetry
                WHERE machine_id = :machine_id
                  AND ts >= :from_ts
                  AND ts <= :to_ts
                ORDER BY ts DESC
                LIMIT :limit
            """)
        
        elif resolution == "5m":
            query = text("""
                SELECT 
                    bucket AS ts,
                    machine_id,
                    rpm_avg AS rpm,
                    rpm_max,
                    rpm_min,
                    feed_avg AS feed_mm_min,
                    feed_max,
                    feed_min,
                    state_mode AS state,
                    sample_count,
                    uptime_ratio
                FROM telemetry_5m
                WHERE machine_id = :machine_id
                  AND bucket >= :from_ts
                  AND bucket <= :to_ts
                ORDER BY bucket DESC
                LIMIT :limit
            """)
        
        elif resolution == "1h":
            query = text("""
                SELECT 
                    bucket AS ts,
                    machine_id,
                    rpm_avg AS rpm,
                    rpm_max,
                    feed_avg AS feed_mm_min,
                    sample_count,
                    uptime_ratio
                FROM telemetry_1h
                WHERE machine_id = :machine_id
                  AND bucket >= :from_ts
                  AND bucket <= :to_ts
                ORDER BY bucket DESC
                LIMIT :limit
            """)
        
        elif resolution == "1d":
            query = text("""
                SELECT 
                    date AS ts,
                    machine_id,
                    rpm_avg AS rpm,
                    rpm_max,
                    feed_avg AS feed_mm_min,
                    sample_count,
                    availability AS uptime_ratio
                FROM telemetry_1d
                WHERE machine_id = :machine_id
                  AND date >= :from_ts::date
                  AND date <= :to_ts::date
                ORDER BY date DESC
            """)
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid resolution: {resolution}. Must be one of: raw, 5m, 1h, 1d"
            )
        
        # Execute query
        result = db.execute(query, {
            "machine_id": machine_id,
            "from_ts": from_dt,
            "to_ts": to_dt,
            "limit": limit
        })
        
        # Format response
        rows = []
        for row in result:
            row_dict = {
                "ts": row.ts.isoformat() if hasattr(row.ts, 'isoformat') else str(row.ts),
                "machine_id": row.machine_id,
                "rpm": round(float(row.rpm), 1) if row.rpm is not None else 0,
                "feed_mm_min": round(float(row.feed_mm_min), 1) if hasattr(row, 'feed_mm_min') and row.feed_mm_min is not None else 0,
            }
            
            # Add optional fields
            if hasattr(row, 'state') and row.state:
                row_dict["state"] = row.state
            
            if hasattr(row, 'rpm_max') and row.rpm_max is not None:
                row_dict["rpm_max"] = round(float(row.rpm_max), 1)
                row_dict["rpm_min"] = round(float(row.rpm_min), 1) if hasattr(row, 'rpm_min') else None
            
            if hasattr(row, 'feed_max') and row.feed_max is not None:
                row_dict["feed_max"] = round(float(row.feed_max), 1)
                row_dict["feed_min"] = round(float(row.feed_min), 1) if hasattr(row, 'feed_min') else None
            
            if hasattr(row, 'sample_count') and row.sample_count is not None:
                row_dict["sample_count"] = int(row.sample_count)
            
            if hasattr(row, 'uptime_ratio') and row.uptime_ratio is not None:
                row_dict["uptime_ratio"] = round(float(row.uptime_ratio), 4)
            
            if hasattr(row, 'sequence') and row.sequence:
                row_dict["sequence"] = int(row.sequence)
            
            rows.append(row_dict)
        
        return {
            "machine_id": machine_id,
            "from_ts": from_ts,
            "to_ts": to_ts,
            "resolution": resolution,
            "count": len(rows),
            "data": rows
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/{machine_id}/history/summary")
def get_history_summary(
    machine_id: str,
    from_ts: str = Query(..., description="Start timestamp (ISO 8601)"),
    to_ts: str = Query(..., description="End timestamp (ISO 8601)"),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get summary statistics for a time period.
    
    Example:
        GET /v1/machines/CNC-SIM-001/history/summary?from_ts=2025-11-01T00:00:00Z&to_ts=2025-11-05T00:00:00Z
    """
    try:
        from_dt = datetime.fromisoformat(from_ts.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(to_ts.replace('Z', '+00:00'))
        
        query = text("""
            SELECT 
                machine_id,
                COUNT(*) AS total_samples,
                AVG(rpm) AS avg_rpm,
                MAX(rpm) AS max_rpm,
                MIN(rpm) AS min_rpm,
                AVG(feed_mm_min) AS avg_feed,
                MAX(feed_mm_min) AS max_feed,
                SUM(CASE WHEN state = 'running' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS uptime_ratio,
                SUM(CASE WHEN state = 'running' THEN 1 ELSE 0 END) AS running_samples,
                SUM(CASE WHEN state = 'stopped' THEN 1 ELSE 0 END) AS stopped_samples,
                SUM(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) AS idle_samples
            FROM telemetry
            WHERE machine_id = :machine_id
              AND ts >= :from_ts
              AND ts <= :to_ts
            GROUP BY machine_id
        """)
        
        result = db.execute(query, {
            "machine_id": machine_id,
            "from_ts": from_dt,
            "to_ts": to_dt
        }).fetchone()
        
        if not result:
            return {
                "machine_id": machine_id,
                "from_ts": from_ts,
                "to_ts": to_ts,
                "message": "No data found for this period"
            }
        
        # Calculate time durations (assuming 2-second sampling)
        total_time_min = (result.total_samples * 2) / 60
        running_time_min = (result.running_samples * 2) / 60
        stopped_time_min = (result.stopped_samples * 2) / 60
        idle_time_min = (result.idle_samples * 2) / 60
        
        return {
            "machine_id": machine_id,
            "from_ts": from_ts,
            "to_ts": to_ts,
            "total_samples": int(result.total_samples),
            "statistics": {
                "rpm": {
                    "avg": round(float(result.avg_rpm), 1) if result.avg_rpm else 0,
                    "max": round(float(result.max_rpm), 1) if result.max_rpm else 0,
                    "min": round(float(result.min_rpm), 1) if result.min_rpm else 0
                },
                "feed_mm_min": {
                    "avg": round(float(result.avg_feed), 1) if result.avg_feed else 0,
                    "max": round(float(result.max_feed), 1) if result.max_feed else 0
                }
            },
            "time_distribution": {
                "total_min": round(total_time_min, 1),
                "running_min": round(running_time_min, 1),
                "stopped_min": round(stopped_time_min, 1),
                "idle_min": round(idle_time_min, 1),
                "uptime_ratio": round(float(result.uptime_ratio), 4) if result.uptime_ratio else 0
            },
            "sample_distribution": {
                "running": int(result.running_samples),
                "stopped": int(result.stopped_samples),
                "idle": int(result.idle_samples)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary calculation failed: {str(e)}")
