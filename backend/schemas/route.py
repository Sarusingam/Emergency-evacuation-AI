"""Pydantic schemas for route endpoints."""
from __future__ import annotations
from pydantic import BaseModel
from typing import Any

class RouteResponse(BaseModel):
    zone_id: str = ""
    exit_id: str = ""
    path: list[str] = []
    cost: float = 0.0
    travel_time: float = 0.0
    distance: float = 0.0
    feasible: bool = True

class EvacuationPlanResponse(BaseModel):
    plan_id: str = ""
    status: str = "pending"
    total_people: int = 0
    people_assigned: int = 0
    assignments: dict[str, Any] = {}
    estimated_time: float = 0.0
    reasoning: str = ""
