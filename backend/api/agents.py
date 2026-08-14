"""Agent status API endpoints."""
from fastapi import APIRouter
from backend.services.emergency_service import emergency_service

router = APIRouter()

@router.get("/status")
def get_agent_status():
    """Get status of all agents."""
    state = emergency_service._state
    agents = [
        {"name": "crowd_agent", "status": "active" if emergency_service.is_active else "idle"},
        {"name": "risk_agent", "status": "active" if emergency_service.is_active else "idle"},
        {"name": "traffic_agent", "status": "active" if emergency_service.is_active else "idle"},
        {"name": "transport_agent", "status": "active" if emergency_service.is_active else "idle"},
        {"name": "route_agent", "status": "active" if emergency_service.is_active else "idle"},
        {"name": "coordinator_agent", "status": "active" if emergency_service.is_active else "idle"},
    ]
    return {
        "agents": agents,
        "workflow_status": "active" if emergency_service.is_active else "idle",
        "replan_count": state.get("replan_count", 0),
    }

@router.get("/messages")
def get_messages():
    """Get all agent messages."""
    return {"messages": emergency_service.get_agent_messages()}

@router.get("/reasoning")
def get_reasoning():
    """Get coordinator reasoning."""
    return {"reasoning": emergency_service._state.get("coordinator_reasoning", "")}
