"""Pydantic schemas for user/evacuee endpoints.

These schemas expose only evacuee-safe information.
No internal agent state, optimization weights, or debug data.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any


class UserStatusResponse(BaseModel):
    """Emergency status visible to evacuees."""
    emergency_active: bool = False
    mode: str = "demo"
    severity: str = ""
    emergency_type: str = ""
    message: str = ""


class UserZoneOption(BaseModel):
    """A zone available for selection by the evacuee."""
    zone_id: str
    zone_name: str


class UserZonesResponse(BaseModel):
    """List of zones for the zone picker."""
    zones: list[UserZoneOption] = []


class UserRouteStep(BaseModel):
    """A single step in the evacuation route."""
    road_id: str = ""
    road_name: str = ""
    blocked: bool = False


class UserRouteResponse(BaseModel):
    """Personalized evacuation instructions for an evacuee."""
    emergency_active: bool = False
    zone_id: str = ""
    zone_name: str = ""
    risk_level: str = "UNKNOWN"
    destination_exit_id: str = ""
    destination_exit_name: str = ""
    route_steps: list[UserRouteStep] = []
    route_summary: str = ""
    eta_minutes: float = 0.0
    roads_to_avoid: list[str] = []
    route_version: int = 0
    last_updated: str = ""
    message: str = ""
    mode: str = "demo"


class UserAlertItem(BaseModel):
    """A single alert relevant to an evacuee."""
    alert_type: str
    message: str
    severity: str = "info"
    timestamp: str = ""


class UserAlertsResponse(BaseModel):
    """Active alerts for evacuees."""
    alerts: list[UserAlertItem] = []
    emergency_active: bool = False


class UserLocationRequest(BaseModel):
    """Browser geolocation coordinates from the evacuee."""
    lat: float
    lon: float


class UserLocationResponse(BaseModel):
    """Resolved zone from coordinates."""
    zone_id: str = ""
    zone_name: str = ""
    distance_meters: float = 0.0
    message: str = ""
