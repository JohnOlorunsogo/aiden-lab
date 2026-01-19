"""REST API endpoints for AIDEN Labs."""
import asyncio
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pathlib import Path

from app.services.database import db
from app.services.gemini import gemini_service
from app.core.detector import error_detector
from app.core.watcher import log_watcher
from app.config import settings
from app.models.error import ErrorListResponse, ErrorWithSolution, Severity
from app.models.device import DeviceListResponse, Device

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "watcher_running": log_watcher.is_running,
        "watch_directory": str(settings.log_watch_dir)
    }


@router.get("/errors", response_model=ErrorListResponse)
async def list_errors(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    device_id: Optional[str] = None,
    severity: Optional[str] = None
):
    """Get paginated list of errors with solutions."""
    sev = Severity(severity) if severity else None
    errors, total = await db.get_errors(
        page=page,
        per_page=per_page,
        device_id=device_id,
        severity=sev
    )
    return ErrorListResponse(
        errors=errors,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/errors/active", response_model=ErrorListResponse)
async def list_active_errors(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get paginated list of non-dismissed errors for dashboard."""
    errors, total = await db.get_active_errors(page=page, per_page=per_page)
    return ErrorListResponse(
        errors=errors,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/errors/{error_id}", response_model=ErrorWithSolution)
async def get_error(error_id: int):
    """Get a specific error with its solution."""
    result = await db.get_error_by_id(error_id)
    if not result:
        raise HTTPException(status_code=404, detail="Error not found")
    return result


@router.post("/errors/{error_id}/dismiss")
async def dismiss_error(error_id: int):
    """Dismiss a single error from the dashboard (still visible in history)."""
    result = await db.dismiss_error(error_id)
    if not result:
        raise HTTPException(status_code=404, detail="Error not found")
    return {"status": "dismissed", "error_id": error_id}


@router.post("/errors/dismiss-all")
async def dismiss_all_errors():
    """Dismiss all errors from the dashboard (still visible in history)."""
    count = await db.dismiss_all_errors()
    return {"status": "dismissed", "count": count}


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices():
    """Get list of monitored devices with stats."""
    stats = await db.get_device_stats()
    devices = []
    
    # Get watched files
    watched_files = log_watcher.get_watched_files()
    
    for stat in stats:
        devices.append(Device(
            id=stat["device_id"],
            log_file=next((f for f in watched_files if stat["device_id"] in f), "unknown"),
            error_count=stat["error_count"],
            last_seen=stat["last_error"] if stat["last_error"] else None
        ))
    
    return DeviceListResponse(devices=devices, total=len(devices))


@router.get("/config")
async def get_config():
    """Get current configuration."""
    return {
        "log_watch_dir": str(settings.log_watch_dir),
        "context_lines": settings.context_lines,
        "error_patterns": error_detector.get_patterns()
    }


@router.put("/config")
async def update_config(
    log_watch_dir: Optional[str] = None,
    context_lines: Optional[int] = None
):
    """Update configuration (runtime only, not persisted)."""
    if log_watch_dir:
        new_dir = Path(log_watch_dir)
        if not new_dir.exists():
            raise HTTPException(status_code=400, detail="Directory does not exist")
        # Would need to restart watcher to apply this
        return {"message": "Restart required to apply directory change"}
    
    if context_lines:
        settings.context_lines = context_lines
    
    return {"status": "updated"}


@router.post("/patterns")
async def add_pattern(pattern: str, severity: str = "warning"):
    """Add a new error detection pattern."""
    try:
        sev = Severity(severity)
        error_detector.add_pattern(pattern, sev)
        return {"status": "added", "pattern": pattern, "severity": severity}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get overall statistics."""
    device_stats = await db.get_device_stats()
    total_errors = sum(s["error_count"] for s in device_stats)
    
    return {
        "total_errors": total_errors,
        "devices_count": len(device_stats),
        "watcher_running": log_watcher.is_running,
        "watched_files": log_watcher.get_watched_files()
    }


@router.post("/reanalyze")
async def reanalyze_errors():
    """Re-analyze all errors that don't have solutions."""
    # Get all errors without solutions
    errors_without_solutions = await db.get_errors_without_solutions()
    
    if not errors_without_solutions:
        return {"status": "no_errors", "message": "All errors already have solutions"}
    
    logger.info(f"Re-analyzing {len(errors_without_solutions)} errors without solutions")
    
    analyzed_count = 0
    failed_count = 0
    
    for error in errors_without_solutions:
        try:
            # Analyze with Gemini
            solution = await gemini_service.analyze_error(error, "")
            solution.error_id = error.id
            
            # Store solution
            await db.insert_solution(solution)
            analyzed_count += 1
            logger.info(f"Successfully analyzed error {error.id}")
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to analyze error {error.id}: {e}")
    
    return {
        "status": "completed",
        "analyzed": analyzed_count,
        "failed": failed_count,
        "total": len(errors_without_solutions)
    }
