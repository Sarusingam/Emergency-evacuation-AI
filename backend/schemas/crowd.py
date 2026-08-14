"""Pydantic schemas for crowd endpoints."""
from __future__ import annotations
from pydantic import BaseModel
from typing import Any

class ZoneCrowdData(BaseModel):
    zone_id: str
    count: int = 0
    density: float = 0.0
    density_level: str = "LOW"
    trend: str = "stable"

class CrowdAnalysisResponse(BaseModel):
    zones: dict[str, Any] = {}
    summary: dict[str, Any] = {}
    timestamp: str = ""
