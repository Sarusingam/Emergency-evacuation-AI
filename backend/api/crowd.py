"""Crowd API endpoints."""
from fastapi import APIRouter
from backend.services.emergency_service import emergency_service

router = APIRouter()

@router.get("/analysis")
def get_crowd_analysis():
    """Get current crowd analysis for all zones."""
    return emergency_service.get_crowd_analysis()

@router.get("/zones")
def get_zones():
    """Get current zone data."""
    return emergency_service.get_zones()

@router.get("/zones/{zone_id}")
def get_zone(zone_id: str):
    """Get data for a specific zone."""
    zones = emergency_service.get_zones()
    return zones.get(zone_id, {"error": f"Zone {zone_id} not found"})
