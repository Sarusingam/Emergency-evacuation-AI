"""Emergency API endpoints."""
from __future__ import annotations
from fastapi import APIRouter
from backend.schemas.emergency import (
    EmergencyCreate, EmergencyResponse, EmergencyStatus,
    BlockRoadRequest, UpdateCrowdRequest,
)
from backend.services.emergency_service import emergency_service

router = APIRouter()

@router.post("/start", response_model=EmergencyResponse)
def start_emergency(request: EmergencyCreate):
    """Start a new emergency and run the agent workflow."""
    result = emergency_service.start_emergency(
        emergency_type=request.emergency_type,
        severity=request.severity,
        scenario=request.scenario,
    )
    return EmergencyResponse(
        emergency_id=result.get("emergency_id", ""),
        emergency_type=result.get("emergency_type", ""),
        severity=result.get("severity", ""),
        status=result.get("status", ""),
        message="Emergency started, agents activated",
    )

@router.get("/status")
def get_status():
    """Get current emergency status."""
    return emergency_service.get_state()

@router.post("/block-road")
def block_road(request: BlockRoadRequest):
    """Block a road (triggers replanning)."""
    return emergency_service.block_road(request.road_id)

@router.post("/update-crowd")
def update_crowd(request: UpdateCrowdRequest):
    """Update crowd count for a zone."""
    return emergency_service.update_crowd(request.zone_id, request.new_count)

@router.post("/step")
def simulation_step():
    """Run one simulation step."""
    return emergency_service.step_simulation()

@router.post("/stop")
def stop_emergency():
    """Stop the current emergency."""
    emergency_service._active = False
    return {"status": "stopped"}
