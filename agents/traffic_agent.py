"""
Traffic Agent — Road Conditions & Congestion Monitoring.

This agent monitors road conditions, detects blocked and congested
roads, and updates traffic status in the shared state.

It reads road data from the scenario and any simulation updates,
then produces a comprehensive traffic status report including:
- Per-road congestion level and classification
- Blocked road detection
- Available capacity estimation
- Flags for roads that need attention

Input: state['roads'] with road definitions.
Output: state['traffic_status'] with per-road traffic conditions.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.agent_messages import MessagePriority, MessageType

logger = logging.getLogger(__name__)

# Congestion thresholds
CONGESTION_THRESHOLDS = {
    "free_flow": 0.2,
    "moderate": 0.4,
    "heavy": 0.7,
    "gridlock": 0.9,
}


def classify_congestion(
    congestion: float,
    thresholds: dict[str, float] | None = None,
) -> str:
    """Classify a congestion value into a categorical level.

    Args:
        congestion: Congestion level 0.0-1.0.
        thresholds: Custom thresholds.

    Returns:
        One of 'FREE_FLOW', 'MODERATE', 'HEAVY', 'GRIDLOCK'.
    """
    t = thresholds or CONGESTION_THRESHOLDS
    if congestion >= t.get("gridlock", 0.9):
        return "GRIDLOCK"
    elif congestion >= t.get("heavy", 0.7):
        return "HEAVY"
    elif congestion >= t.get("moderate", 0.4):
        return "MODERATE"
    else:
        return "FREE_FLOW"


class TrafficAgent(BaseAgent):
    """Agent responsible for monitoring road conditions.

    Analyzes all roads in the scenario to determine congestion
    levels, detect blocked roads, and estimate available capacity.
    Sends alerts for roads that are near gridlock or blocked.
    """

    def __init__(self) -> None:
        """Initialize the Traffic Agent."""
        super().__init__(
            name="traffic_agent",
            description="Monitors road conditions and traffic congestion",
        )

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Analyze traffic conditions for all roads.

        Steps:
            1. Read road data from state.
            2. Classify congestion for each road.
            3. Detect blocked roads.
            4. Estimate available capacity.
            5. Generate alerts for critical conditions.

        Args:
            state: The full EvacuationState dict.

        Returns:
            State update with 'traffic_status' and alert messages.
        """
        self._log_action("processing", "Analyzing traffic conditions")

        roads = state.get("roads", {})
        if not roads:
            self._log_warning("no roads", "No road data available")
            return {
                "traffic_status": {"roads": {}, "summary": {}},
                "messages": [
                    self._create_message(
                        message_type=MessageType.TRAFFIC_UPDATE,
                        description="No road data available",
                        priority=MessagePriority.LOW,
                    )
                ],
            }

        road_analysis: dict[str, dict[str, Any]] = {}
        messages: list[dict[str, Any]] = []
        blocked_roads: list[str] = []
        congested_roads: list[str] = []
        needs_replan = False
        replan_reason = ""

        for road_id, road_data in roads.items():
            blocked = road_data.get("blocked", False)
            # Use current congestion, fallback to initial_congestion
            congestion = road_data.get(
                "congestion",
                road_data.get("initial_congestion", 0.0),
            )
            capacity = road_data.get("capacity", 500)

            # Classify
            if blocked:
                congestion_level = "BLOCKED"
                available_capacity = 0
            else:
                congestion_level = classify_congestion(congestion)
                # Available capacity decreases with congestion
                available_capacity = int(capacity * (1.0 - congestion))

            road_result = {
                "road_id": road_id,
                "name": road_data.get("name", road_id),
                "from_node": road_data.get("from_node", ""),
                "to_node": road_data.get("to_node", ""),
                "blocked": blocked,
                "congestion": round(congestion, 3),
                "congestion_level": congestion_level,
                "capacity": capacity,
                "available_capacity": available_capacity,
                "travel_time": road_data.get("travel_time", 0.0),
                "timestamp": self._now_iso(),
            }
            road_analysis[road_id] = road_result

            if blocked:
                blocked_roads.append(road_id)
                needs_replan = True
                replan_reason = f"Road {road_id} is blocked"
            elif congestion >= 0.8:
                congested_roads.append(road_id)

        # Generate alerts for blocked roads
        if blocked_roads:
            messages.append(
                self._create_message(
                    message_type=MessageType.ALERT,
                    payload={
                        "alert_type": "road_blocked",
                        "roads": blocked_roads,
                    },
                    priority=MessagePriority.CRITICAL,
                    description=f"Roads BLOCKED: {', '.join(blocked_roads)}",
                )
            )

        # Alert for heavily congested roads
        if congested_roads:
            messages.append(
                self._create_message(
                    message_type=MessageType.ALERT,
                    payload={
                        "alert_type": "heavy_congestion",
                        "roads": congested_roads,
                    },
                    priority=MessagePriority.HIGH,
                    description=f"Heavy congestion on: {', '.join(congested_roads)}",
                )
            )

        # Standard traffic update
        messages.append(
            self._create_message(
                message_type=MessageType.TRAFFIC_UPDATE,
                payload={
                    "roads_analyzed": len(road_analysis),
                    "blocked_roads": blocked_roads,
                    "congested_roads": congested_roads,
                },
                priority=MessagePriority.MEDIUM,
                description=f"Traffic analysis: {len(blocked_roads)} blocked, {len(congested_roads)} congested",
            )
        )

        self._log_action(
            "completed",
            f"{len(blocked_roads)} blocked, {len(congested_roads)} congested",
        )

        result: dict[str, Any] = {
            "traffic_status": {
                "roads": road_analysis,
                "summary": {
                    "total_roads": len(road_analysis),
                    "blocked_roads": blocked_roads,
                    "congested_roads": congested_roads,
                },
                "timestamp": self._now_iso(),
            },
            "messages": messages,
        }

        # Flag for replanning if roads are blocked
        if needs_replan:
            result["needs_replan"] = True
            result["replan_reason"] = replan_reason

        return result
