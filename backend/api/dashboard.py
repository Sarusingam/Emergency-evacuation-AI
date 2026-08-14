"""Dashboard API — Aggregated summary endpoint."""
from fastapi import APIRouter
from backend.services.emergency_service import emergency_service

router = APIRouter()

@router.get("/summary")
def get_dashboard_summary():
    """Get a single aggregated view for the dashboard."""
    state = emergency_service.get_state()
    crowd = emergency_service.get_crowd_analysis()
    risk = emergency_service.get_risk_assessment()
    traffic = emergency_service.get_traffic_status()
    transport = emergency_service.get_transport_status()
    plan = emergency_service.get_evacuation_plan()
    zones = emergency_service.get_zones()
    roads = emergency_service.get_roads()
    exits = emergency_service.get_exits()
    vehicles = emergency_service.get_vehicles()

    return {
        "state": state,
        "crowd_analysis": crowd,
        "risk_assessment": risk,
        "traffic_status": traffic,
        "transport_status": transport,
        "evacuation_plan": plan,
        "zones": zones,
        "roads": roads,
        "exits": exits,
        "vehicles": vehicles,
    }
