"""Pydantic schemas for emergency endpoints."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any


class EmergencyCreate(BaseModel):
    emergency_type: str = "general"
    severity: str = "high"
    description: str = ""
    scenario: str = "default_demo"

class EmergencyResponse(BaseModel):
    emergency_id: str
    emergency_type: str
    severity: str
    status: str
    message: str = ""

class EmergencyStatus(BaseModel):
    emergency_id: str
    status: str
    emergency_type: str
    severity: str
    total_people: int = 0
    evacuated: int = 0
    progress: float = 0.0
    plan: dict[str, Any] = {}
    reasoning: str = ""

class BlockRoadRequest(BaseModel):
    road_id: str
    reason: str = "manual_block"

class UpdateCrowdRequest(BaseModel):
    zone_id: str
    new_count: int
