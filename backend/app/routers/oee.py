# backend/app/routers/oee.py
# OEE API endpoints

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import csv
import io

from ..db import get_db
from ..services.oee import calculate_oee, calculate_oee_trend, get_oee_benchmark

router = APIRouter(prefix="/v1/machines", tags=["oee"])


@router.get("/{machine_id}/oee")
def get_machine_oee(
    machine_id: str,
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), default: today"),
    shift: str = Query("daily", description="morning, afternoon, night, or daily"),
    db: Session = Depends(get_db)
):
    """
    Get OEE for a specific machine, date, and shift.
    
    Example:
        GET /v1/machines/CNC-SIM-001/oee?date=2025-11-05&shift=daily
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        oee_data = calculate_oee(db, machine_id, date, shift)
        
        # Add benchmark classification
        benchmark = get_oee_benchmark(oee_data["oee"])
        oee_data["benchmark"] = benchmark
        
        return oee_data
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OEE calculation failed: {str(e)}")


@router.get("/{machine_id}/oee/trend")
def get_machine_oee_trend(
    machine_id: str,
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    shift: str = Query("daily", description="morning, afternoon, night, or daily"),
    db: Session = Depends(get_db)
):
    """
    Get OEE trend over a date range.
    
    Example:
        GET /v1/machines/CNC-SIM-001/oee/trend?from_date=2025-11-01&to_date=2025-11-07
    """
    if from_date is None:
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    if to_date is None:
        to_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        trend_data = calculate_oee_trend(db, machine_id, from_date, to_date, shift)
        
        # Add benchmarks
        for item in trend_data:
            item["benchmark"] = get_oee_benchmark(item["oee"])
        
        return {
            "machine_id": machine_id,
            "from_date": from_date,
            "to_date": to_date,
            "shift": shift,
            "trend": trend_data
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OEE trend calculation failed: {str(e)}")


@router.get("/{machine_id}/oee/export")
def export_machine_oee(
    machine_id: str,
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    format: str = Query("csv", description="csv or json"),
    shift: str = Query("daily"),
    db: Session = Depends(get_db)
):
    """
    Export OEE data as CSV or JSON.
    
    Example:
        GET /v1/machines/CNC-SIM-001/oee/export?format=csv&from_date=2025-11-01&to_date=2025-11-07
    """
    if from_date is None:
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    if to_date is None:
        to_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        trend_data = calculate_oee_trend(db, machine_id, from_date, to_date, shift)
        
        if format == "csv":
            # Generate CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "date", "machine_id", "shift", 
                "planned_time_min", "operating_time_min",
                "availability", "performance", "quality", "oee"
            ])
            writer.writeheader()
            
            for item in trend_data:
                writer.writerow({
                    "date": item["date"],
                    "machine_id": item["machine_id"],
                    "shift": item["shift"],
                    "planned_time_min": item["planned_time_min"],
                    "operating_time_min": item["operating_time_min"],
                    "availability": item["availability"],
                    "performance": item["performance"],
                    "quality": item["quality"],
                    "oee": item["oee"]
                })
            
            csv_content = output.getvalue()
            
            from fastapi.responses import Response
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=oee_{machine_id}_{from_date}_{to_date}.csv"
                }
            )
        
        else:  # JSON
            return {
                "machine_id": machine_id,
                "from_date": from_date,
                "to_date": to_date,
                "format": "json",
                "data": trend_data
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
