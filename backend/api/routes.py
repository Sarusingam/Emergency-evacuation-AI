"""Routes API endpoints."""
from fastapi import APIRouter
from backend.services.emergency_service import emergency_service

router = APIRouter()

@router.get("/")
def get_routes():
    """Get all computed evacuation routes."""
    return emergency_service.get_evacuation_routes()

@router.get("/plan")
def get_plan():
    """Get the current evacuation plan."""
    return emergency_service.get_evacuation_plan()

@router.get("/exits")
def get_exits():
    """Get all exit data."""
    return emergency_service.get_exits()
