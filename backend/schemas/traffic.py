"""Pydantic schemas for traffic endpoints."""
from __future__ import annotations
from pydantic import BaseModel
from typing import Any

class RoadStatus(BaseModel):
    road_id: str
    name: str = ""
    blocked: bool = False
    congestion: float = 0.0
    congestion_level: str = "FREE_FLOW"
    capacity: int = 0
    available_capacity: int = 0

class TrafficStatusResponse(BaseModel):
    roads: dict[str, Any] = {}
    summary: dict[str, Any] = {}
