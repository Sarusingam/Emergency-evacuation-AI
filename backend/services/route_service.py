"""Route Service — Wrapper for route/plan data."""
from __future__ import annotations
from typing import Any
from backend.services.emergency_service import emergency_service


class RouteQueryService:
    def get_routes(self) -> dict[str, Any]:
        return emergency_service.get_evacuation_routes()

    def get_plan(self) -> dict[str, Any]:
        return emergency_service.get_evacuation_plan()


route_query_service = RouteQueryService()
