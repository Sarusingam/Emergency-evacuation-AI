"""Pydantic schemas for agent endpoints."""
from __future__ import annotations
from pydantic import BaseModel
from typing import Any

class AgentStatusResponse(BaseModel):
    name: str
    status: str = "idle"
    last_run: str = ""
    output: dict[str, Any] = {}

class AgentWorkflowResponse(BaseModel):
    status: str = "idle"
    agents: list[AgentStatusResponse] = []
    messages: list[dict[str, Any]] = []
    replan_count: int = 0
