"""
Transport Agent — Vehicle Tracking & Assignment.

This agent manages evacuation vehicles (buses, ambulances, vans),
tracks their status, and assigns them to zones based on need.

Assignment priority is based on:
- Zone crowd count (more people → higher priority)
- Zone risk level (higher risk → higher priority)
- Vehicle proximity (closer vehicle → preferred)
- Vehicle capacity vs. need

Input: state['vehicles'], state['zones'], state['crowd_analysis'],
       state['risk_assessment'].
Output: state['transport_status'] with vehicle assignments and capacity.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.agent_messages import MessagePriority, MessageType

logger = logging.getLogger(__name__)

# Priority weights for zone-to-vehicle assignment
ASSIGNMENT_WEIGHTS = {
    "crowd_count": 0.4,
    "risk_level": 0.4,
    "proximity": 0.2,
}

# Risk level to numeric value
RISK_LEVEL_VALUE = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.5,
    "LOW": 0.25,
}


class TransportAgent(BaseAgent):
    """Agent responsible for vehicle tracking and assignment.

    Monitors all evacuation vehicles, assigns available vehicles
    to zones based on need priority, and reports transport capacity.
    """

    def __init__(self) -> None:
        """Initialize the Transport Agent."""
        super().__init__(
            name="transport_agent",
            description="Tracks vehicles and assigns them to evacuation zones",
        )

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Process vehicle assignments.

        Steps:
            1. Read vehicle and zone data.
            2. Score zones by priority (crowd + risk).
            3. Assign available vehicles to highest-priority zones.
            4. Report vehicle status and total transport capacity.

        Args:
            state: The full EvacuationState dict.

        Returns:
            State update with 'transport_status' and messages.
        """
        self._log_action("processing", "Managing vehicle assignments")

        vehicles = state.get("vehicles", {})
        zones = state.get("zones", {})
        crowd_analysis = state.get("crowd_analysis", {})
        risk_assessment = state.get("risk_assessment", {})

        if not vehicles:
            self._log_warning("no vehicles", "No vehicle data available")
            return {
                "transport_status": {"vehicles": {}, "summary": {}},
                "messages": [
                    self._create_message(
                        message_type=MessageType.TRANSPORT_UPDATE,
                        description="No vehicle data available",
                        priority=MessagePriority.LOW,
                    )
                ],
            }

        # 1. Score zones by priority
        zone_priorities = self._score_zones(
            zones, crowd_analysis, risk_assessment
        )

        # 2. Process vehicles and track assignments
        vehicle_status: dict[str, dict[str, Any]] = {}
        available_vehicles: list[str] = []
        dispatched_vehicles: list[str] = []
        total_capacity = 0

        for vehicle_id, vehicle_data in vehicles.items():
            status = vehicle_data.get("status", "available")
            capacity = vehicle_data.get("capacity", 0)

            vehicle_info = {
                "vehicle_id": vehicle_id,
                "type": vehicle_data.get("type", "unknown"),
                "capacity": capacity,
                "status": status,
                "assigned_zone": vehicle_data.get("assigned_zone"),
                "lat": vehicle_data.get("lat", 0.0),
                "lon": vehicle_data.get("lon", 0.0),
            }

            if status == "available":
                available_vehicles.append(vehicle_id)
                total_capacity += capacity
            elif status in ("dispatched", "en_route", "loading"):
                dispatched_vehicles.append(vehicle_id)

            vehicle_status[vehicle_id] = vehicle_info

        # 3. Assign available vehicles to priority zones
        assignments = self._assign_vehicles(
            available_vehicles, vehicles, zone_priorities, zones
        )

        # Update vehicle status with new assignments
        for assignment in assignments:
            vid = assignment["vehicle_id"]
            if vid in vehicle_status:
                vehicle_status[vid]["assigned_zone"] = assignment["zone_id"]
                vehicle_status[vid]["status"] = "dispatched"

        # 4. Build summary
        summary = {
            "total_vehicles": len(vehicles),
            "available": len(available_vehicles) - len(assignments),
            "dispatched": len(dispatched_vehicles) + len(assignments),
            "new_assignments": len(assignments),
            "total_available_capacity": total_capacity,
            "zone_priorities": zone_priorities,
        }

        # Generate messages
        messages: list[dict[str, Any]] = []

        if assignments:
            messages.append(
                self._create_message(
                    message_type=MessageType.TRANSPORT_UPDATE,
                    payload={
                        "assignments": assignments,
                    },
                    priority=MessagePriority.HIGH,
                    description=f"Dispatched {len(assignments)} vehicles to priority zones",
                )
            )

        messages.append(
            self._create_message(
                message_type=MessageType.TRANSPORT_UPDATE,
                payload=summary,
                priority=MessagePriority.MEDIUM,
                description=f"Transport status: {summary['available']} available, {summary['dispatched']} dispatched",
            )
        )

        self._log_action(
            "completed",
            f"{len(assignments)} new assignments, {summary['available']} vehicles available",
        )

        return {
            "transport_status": {
                "vehicles": vehicle_status,
                "assignments": assignments,
                "summary": summary,
                "timestamp": self._now_iso(),
            },
            "messages": messages,
        }

    def _score_zones(
        self,
        zones: dict[str, dict],
        crowd_analysis: dict[str, Any],
        risk_assessment: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Score zones by evacuation priority.

        Args:
            zones: Zone data.
            crowd_analysis: Crowd analysis results.
            risk_assessment: Risk assessment results.

        Returns:
            Sorted list of zone priority dicts (highest first).
        """
        priorities: list[dict[str, Any]] = []
        crowd_zones = crowd_analysis.get("zones", {})
        risk_zones = risk_assessment.get("zones", {})

        max_crowd = max(
            (z.get("crowd_count", 0) for z in zones.values()),
            default=1,
        )

        for zone_id, zone_data in zones.items():
            crowd_count = zone_data.get("crowd_count", 0)
            crowd_norm = crowd_count / max(max_crowd, 1)

            risk_info = risk_zones.get(zone_id, {})
            risk_score = risk_info.get("risk_score", 0.0)

            # Composite priority score
            priority = (
                ASSIGNMENT_WEIGHTS["crowd_count"] * crowd_norm
                + ASSIGNMENT_WEIGHTS["risk_level"] * risk_score
            )

            priorities.append({
                "zone_id": zone_id,
                "priority_score": round(priority, 3),
                "crowd_count": crowd_count,
                "risk_level": risk_info.get("risk_level", "unknown"),
            })

        priorities.sort(key=lambda p: p["priority_score"], reverse=True)
        return priorities

    def _assign_vehicles(
        self,
        available_vehicles: list[str],
        vehicles: dict[str, dict],
        zone_priorities: list[dict[str, Any]],
        zones: dict[str, dict],
    ) -> list[dict[str, Any]]:
        """Assign available vehicles to highest-priority zones.

        Simple greedy algorithm: assign vehicles to the highest-
        priority zones first, one vehicle per zone per cycle.

        Args:
            available_vehicles: List of available vehicle IDs.
            vehicles: Full vehicle data.
            zone_priorities: Sorted zone priority list.
            zones: Zone data.

        Returns:
            List of assignment dicts with vehicle_id and zone_id.
        """
        if not available_vehicles or not zone_priorities:
            return []

        assignments: list[dict[str, Any]] = []
        remaining_vehicles = list(available_vehicles)

        for zone_info in zone_priorities:
            if not remaining_vehicles:
                break

            zone_id = zone_info["zone_id"]
            crowd_count = zone_info.get("crowd_count", 0)

            # Only dispatch if zone has significant crowd
            if crowd_count < 20:
                continue

            # Assign the first available vehicle
            vehicle_id = remaining_vehicles.pop(0)
            vehicle_data = vehicles.get(vehicle_id, {})

            assignments.append({
                "vehicle_id": vehicle_id,
                "zone_id": zone_id,
                "vehicle_type": vehicle_data.get("type", "unknown"),
                "capacity": vehicle_data.get("capacity", 0),
                "priority_score": zone_info["priority_score"],
            })

        return assignments
