"""Simulation API endpoints."""
from fastapi import APIRouter
from backend.services.simulation_service import simulation_service

router = APIRouter()

@router.post("/step")
def simulation_step():
    """Run one simulation step."""
    return simulation_service.step()

@router.get("/summary")
def get_summary():
    """Get simulation summary."""
    return simulation_service.get_summary()

@router.get("/history")
def get_history():
    """Get simulation step history."""
    return {"history": simulation_service.get_history()}
