"""Crowd Service — Thin wrapper around emergency service for crowd data."""
from __future__ import annotations
from typing import Any
from backend.services.emergency_service import emergency_service


class CrowdService:
    def get_analysis(self) -> dict[str, Any]:
        return emergency_service.get_crowd_analysis()

    def get_zone_data(self, zone_id: str) -> dict[str, Any]:
        zones = emergency_service.get_crowd_analysis().get("zones", {})
        return zones.get(zone_id, {"error": f"Zone {zone_id} not found"})


crowd_service = CrowdService()
