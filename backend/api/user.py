"""User / Evacuee API endpoints.

These endpoints expose only evacuee-safe information.
No internal agent state, optimization weights, database records,
or debug data is returned.

Users CANNOT:
- block roads
- trigger replanning
- alter evacuation plans
- modify crowd counts
- stop emergencies
"""
from __future__ import annotations
from fastapi import APIRouter
from backend.schemas.user import (
    UserStatusResponse,
    UserRouteResponse,
    UserRouteStep,
    UserZonesResponse,
    UserZoneOption,
    UserAlertsResponse,
    UserAlertItem,
    UserLocationRequest,
    UserLocationResponse,
)
from backend.services.emergency_service import emergency_service

router = APIRouter()


@router.get("/map-data")
def get_user_map_data(zone_id: str = ""):
    """Get all map data needed for the user Leaflet map.

    Returns zone markers, exit markers, route polyline coordinates,
    blocked road segments, and the map center. All coordinates are
    resolved from the current evacuation plan — no route calculation
    is done on the frontend.
    """
    return emergency_service.get_user_map_data(zone_id)


@router.get("/status", response_model=UserStatusResponse)
def get_user_status():
    """Get emergency status for evacuees.

    Returns only whether an emergency is active, its type/severity,
    and the operating mode. No internal details.
    """
    state = emergency_service.get_state()
    active = emergency_service.is_active

    if active:
        message = "Emergency evacuation is in progress. Follow your evacuation instructions."
    else:
        message = "No active emergency. Stay alert and follow official instructions."

    return UserStatusResponse(
        emergency_active=active,
        mode="demo",
        severity=state.get("severity", ""),
        emergency_type=state.get("emergency_type", ""),
        message=message,
    )


@router.get("/zones", response_model=UserZonesResponse)
def get_user_zones():
    """Get available zones for manual location selection.

    Returns zone IDs and human-readable names only.
    No crowd counts, areas, or internal metrics.
    """
    zones = emergency_service.get_zones()
    if not zones:
        zones = emergency_service._scenario_data.get("zones", {})

    zone_list = [
        UserZoneOption(
            zone_id=zone_id,
            zone_name=zone_data.get("name", zone_id),
        )
        for zone_id, zone_data in zones.items()
    ]
    return UserZonesResponse(zones=zone_list)


@router.get("/route")
def get_user_route(zone_id: str = ""):
    """Get personalized evacuation instructions for a zone.

    All route data is derived from the existing AI-generated
    evacuation plan. This endpoint does NOT invent routes.

    Args:
        zone_id: The zone the evacuee is in.
    """
    if not zone_id:
        return UserRouteResponse(
            emergency_active=emergency_service.is_active,
            message="Select your location to receive evacuation instructions.",
            mode="demo",
        )

    data = emergency_service.get_user_route(zone_id)

    return UserRouteResponse(
        emergency_active=data.get("emergency_active", False),
        zone_id=data.get("zone_id", ""),
        zone_name=data.get("zone_name", ""),
        risk_level=data.get("risk_level", "UNKNOWN"),
        destination_exit_id=data.get("destination_exit_id", ""),
        destination_exit_name=data.get("destination_exit_name", ""),
        route_steps=[
            UserRouteStep(**step) for step in data.get("route_steps", [])
        ],
        route_summary=data.get("route_summary", ""),
        eta_minutes=data.get("eta_minutes", 0.0),
        roads_to_avoid=data.get("roads_to_avoid", []),
        route_version=data.get("route_version", 0),
        last_updated=data.get("last_updated", ""),
        message=data.get("message", ""),
        mode=data.get("mode", "demo"),
    )


@router.get("/alerts", response_model=UserAlertsResponse)
def get_user_alerts():
    """Get active alerts relevant to evacuees.

    Returns human-readable alerts about blocked roads,
    congestion, and critical risk zones.
    """
    alerts_data = emergency_service.get_user_alerts()
    return UserAlertsResponse(
        alerts=[UserAlertItem(**a) for a in alerts_data],
        emergency_active=emergency_service.is_active,
    )


@router.post("/location", response_model=UserLocationResponse)
def resolve_location(request: UserLocationRequest):
    """Resolve browser geolocation to nearest evacuation zone.

    Uses Haversine distance to map coordinates to the closest
    zone center. In demo mode, accuracy is limited to ~200m
    zone radii.
    """
    result = emergency_service.resolve_location(request.lat, request.lon)
    return UserLocationResponse(
        zone_id=result.get("zone_id", ""),
        zone_name=result.get("zone_name", ""),
        distance_meters=result.get("distance_meters", 0.0),
        message=result.get("message", ""),
    )
