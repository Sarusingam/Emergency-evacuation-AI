"""Traffic API endpoints."""
from fastapi import APIRouter
from backend.services.emergency_service import emergency_service

router = APIRouter()

@router.get("/")
def get_traffic():
    """Get current traffic status for all roads."""
    return emergency_service.get_traffic_status()

@router.get("/roads")
def get_roads():
    """Get current road data."""
    return emergency_service.get_roads()

@router.get("/roads/{road_id}")
def get_road(road_id: str):
    """Get data for a specific road."""
    roads = emergency_service.get_roads()
    return roads.get(road_id, {"error": f"Road {road_id} not found"})
