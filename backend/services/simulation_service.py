"""Simulation Service — Wrapper for simulation control."""
from __future__ import annotations
from typing import Any
from backend.services.emergency_service import emergency_service


class SimulationService:
    def step(self) -> dict[str, Any]:
        return emergency_service.step_simulation()

    def get_summary(self) -> dict[str, Any]:
        return emergency_service.simulator.get_summary()

    def get_history(self) -> list[dict[str, Any]]:
        return emergency_service.simulator.evac_sim.history


simulation_service = SimulationService()
