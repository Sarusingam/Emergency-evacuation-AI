"""
Agent State Definition for LangGraph Workflow.

This module defines the shared state that flows through the LangGraph
agent workflow. Each agent node reads from and writes to this state.

LangGraph requires TypedDict for state definition. Fields with
Annotated[list, operator.add] accumulate values across nodes;
other fields are overwritten by the last node that sets them.

Input: Initialized from scenario data (zones, roads, exits, vehicles).
Output: Progressively enriched by each agent with analysis results.
"""

from __future__ import annotations

import operator
from typing import Any, Annotated, TypedDict


class ZoneData(TypedDict, total=False):
    """Data structure for a single zone.

    Attributes:
        id: Unique zone identifier.
        name: Human-readable zone name.
        center_lat: Latitude of zone center.
        center_lon: Longitude of zone center.
        radius: Zone radius in meters.
        crowd_count: Current estimated number of people.
        area: Zone area in square meters.
    """
    id: str
    name: str
    center_lat: float
    center_lon: float
    radius: float
    crowd_count: int
    area: float


class RoadData(TypedDict, total=False):
    """Data structure for a single road segment.

    Attributes:
        id: Unique road identifier.
        name: Human-readable road name.
        from_node: Source node (zone_id or exit_id).
        to_node: Destination node (zone_id or exit_id).
        length: Road length in meters.
        travel_time: Estimated travel time in minutes.
        capacity: Maximum number of people the road can handle.
        congestion: Congestion level from 0.0 (free) to 1.0 (gridlock).
        risk: Risk level from 0.0 (safe) to 1.0 (dangerous).
        blocked: Whether the road is completely blocked.
    """
    id: str
    name: str
    from_node: str
    to_node: str
    length: float
    travel_time: float
    capacity: int
    congestion: float
    risk: float
    blocked: bool


class ExitData(TypedDict, total=False):
    """Data structure for an evacuation exit point.

    Attributes:
        id: Unique exit identifier.
        name: Human-readable exit name.
        lat: Latitude.
        lon: Longitude.
        capacity: Maximum number of people that can exit.
        flow_rate: People per minute throughput.
        current_load: Current number of people assigned/using this exit.
    """
    id: str
    name: str
    lat: float
    lon: float
    capacity: int
    flow_rate: int
    current_load: int


class VehicleData(TypedDict, total=False):
    """Data structure for an evacuation vehicle.

    Attributes:
        id: Unique vehicle identifier.
        type: Vehicle type (bus, ambulance, van).
        capacity: Passenger capacity.
        lat: Current latitude.
        lon: Current longitude.
        assigned_zone: Zone this vehicle is assigned to, or None.
        status: Vehicle status (available, dispatched, en_route, loading, returning).
    """
    id: str
    type: str
    capacity: int
    lat: float
    lon: float
    assigned_zone: str | None
    status: str


class EvacuationState(TypedDict, total=False):
    """Shared state for the LangGraph evacuation workflow.

    This TypedDict flows through all agent nodes. Each node reads
    the fields it needs and returns a dict with the fields it updates.

    The 'messages' field uses Annotated[list, operator.add] so that
    messages from all agents accumulate rather than being overwritten.

    All other fields are overwritten by the last node that sets them.

    Sections:
        Emergency Info: Type, severity, and status of the emergency.
        Core Data: Zones, roads, exits, and vehicles from the scenario.
        Agent Outputs: Analysis results produced by each agent.
        Communication: Accumulated agent messages.
        Control Flow: Flags for replanning and simulation step tracking.
        Metadata: Timestamps and coordinator reasoning.
    """

    # ── Emergency Info ──────────────────────────────────────────
    emergency_id: str
    emergency_type: str
    emergency_severity: str  # low, medium, high, critical
    emergency_status: str    # inactive, active, resolved

    # ── Core Data (loaded from scenario) ────────────────────────
    zones: dict[str, dict[str, Any]]
    roads: dict[str, dict[str, Any]]
    exits: dict[str, dict[str, Any]]
    vehicles: dict[str, dict[str, Any]]

    # ── Agent Outputs ───────────────────────────────────────────
    # Crowd Agent output: per-zone crowd counts, density, trends
    crowd_analysis: dict[str, Any]

    # Risk Agent output: per-zone risk levels and scores
    risk_assessment: dict[str, Any]

    # Traffic Agent output: per-road status, blocked/congested roads
    traffic_status: dict[str, Any]

    # Transport Agent output: vehicle assignments and capacity
    transport_status: dict[str, Any]

    # Route Agent output: computed routes from zones to exits
    evacuation_routes: dict[str, Any]

    # Coordinator output: final approved evacuation plan
    evacuation_plan: dict[str, Any]

    # ── Communication ───────────────────────────────────────────
    # Messages accumulate across all nodes (operator.add reducer)
    messages: Annotated[list[dict[str, Any]], operator.add]

    # ── Control Flow ────────────────────────────────────────────
    simulation_step: int
    needs_replan: bool
    replan_reason: str
    replan_count: int
    max_replan_cycles: int

    # ── Metadata ────────────────────────────────────────────────
    last_updated: str
    coordinator_reasoning: str


def create_initial_state(
    emergency_id: str = "emergency_001",
    emergency_type: str = "general",
    emergency_severity: str = "high",
    zones: dict[str, dict] | None = None,
    roads: dict[str, dict] | None = None,
    exits: dict[str, dict] | None = None,
    vehicles: dict[str, dict] | None = None,
    max_replan_cycles: int = 10,
) -> EvacuationState:
    """Create a properly initialized EvacuationState.

    This factory function ensures all required fields have sensible
    defaults so that agent nodes don't encounter missing keys.

    Args:
        emergency_id: Unique identifier for this emergency.
        emergency_type: Type of emergency (e.g., chemical_spill, fire).
        emergency_severity: Severity level (low, medium, high, critical).
        zones: Zone data dict, keyed by zone_id.
        roads: Road data dict, keyed by road_id.
        exits: Exit data dict, keyed by exit_id.
        vehicles: Vehicle data dict, keyed by vehicle_id.
        max_replan_cycles: Maximum number of replanning cycles.

    Returns:
        A fully initialized EvacuationState dict.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    return EvacuationState(
        emergency_id=emergency_id,
        emergency_type=emergency_type,
        emergency_severity=emergency_severity,
        emergency_status="active",
        zones=zones or {},
        roads=roads or {},
        exits=exits or {},
        vehicles=vehicles or {},
        crowd_analysis={},
        risk_assessment={},
        traffic_status={},
        transport_status={},
        evacuation_routes={},
        evacuation_plan={},
        messages=[],
        simulation_step=0,
        needs_replan=False,
        replan_reason="",
        replan_count=0,
        max_replan_cycles=max_replan_cycles,
        last_updated=now,
        coordinator_reasoning="",
    )
