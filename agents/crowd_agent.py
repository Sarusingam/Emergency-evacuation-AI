"""
Crowd Agent — Crowd Monitoring & Density Analysis.

This agent processes crowd data (from computer vision or simulation)
and produces per-zone crowd counts, density levels, and trends.

It reads zone data from the state and enriches it with:
- Estimated crowd count per zone
- Density calculation (people per square meter)
- Density classification (LOW/MODERATE/HIGH/CRITICAL)
- Trend detection (increasing/stable/decreasing)

Input: state['zones'] with zone definitions (area, crowd_count).
Output: state['crowd_analysis'] with per-zone crowd metrics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent
from agents.agent_messages import MessagePriority, MessageType

logger = logging.getLogger(__name__)

# Default density thresholds (people per m²)
DENSITY_THRESHOLDS = {
    "low": 0.5,
    "moderate": 1.0,
    "high": 2.0,
    "critical": 3.0,
}


def classify_density(density: float, thresholds: dict[str, float] | None = None) -> str:
    """Classify a density value into a categorical level.

    Args:
        density: People per square meter.
        thresholds: Custom thresholds. Defaults to DENSITY_THRESHOLDS.

    Returns:
        One of 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'.
    """
    t = thresholds or DENSITY_THRESHOLDS
    if density >= t.get("critical", 3.0):
        return "CRITICAL"
    elif density >= t.get("high", 2.0):
        return "HIGH"
    elif density >= t.get("moderate", 1.0):
        return "MODERATE"
    else:
        return "LOW"


class CrowdAgent(BaseAgent):
    """Agent responsible for crowd monitoring and density analysis.

    Reads zone data (including crowd_count and area) from the shared
    state, calculates density and trends, and publishes results to
    the 'crowd_analysis' state field.

    The agent also detects abnormal density situations and sends
    alert messages to trigger potential replanning.
    """

    def __init__(self) -> None:
        """Initialize the Crowd Agent."""
        super().__init__(
            name="crowd_agent",
            description="Monitors crowd density and movement across zones",
        )
        # Track previous counts for trend detection
        self._previous_counts: dict[str, int] = {}

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Analyze crowd data for all zones.

        Steps:
            1. Read zone data (crowd_count, area).
            2. Calculate density per zone.
            3. Classify density level.
            4. Detect trends vs. previous step.
            5. Generate alerts for critical zones.

        Args:
            state: The full EvacuationState dict.

        Returns:
            State update with 'crowd_analysis' and any alert messages.
        """
        self._log_action("processing", "Analyzing crowd data across all zones")

        zones = state.get("zones", {})
        if not zones:
            self._log_warning("no zones", "No zone data available")
            return {
                "crowd_analysis": {"zones": {}, "summary": "No zones defined"},
                "messages": [
                    self._create_message(
                        message_type=MessageType.CROWD_UPDATE,
                        description="No zone data available for crowd analysis",
                        priority=MessagePriority.LOW,
                    )
                ],
            }

        zone_analysis: dict[str, dict[str, Any]] = {}
        alerts: list[dict[str, Any]] = []
        total_people = 0
        critical_zones: list[str] = []
        high_density_zones: list[str] = []

        for zone_id, zone_data in zones.items():
            crowd_count = zone_data.get("crowd_count", 0)
            area = zone_data.get("area", 1.0)  # Avoid division by zero

            # Calculate density
            density = crowd_count / max(area, 1.0)
            density_level = classify_density(density)

            # Detect trend
            prev_count = self._previous_counts.get(zone_id, crowd_count)
            if crowd_count > prev_count * 1.1:
                trend = "increasing"
            elif crowd_count < prev_count * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"

            # Update previous counts
            self._previous_counts[zone_id] = crowd_count
            total_people += crowd_count

            zone_result = {
                "zone_id": zone_id,
                "count": crowd_count,
                "area": area,
                "density": round(density, 4),
                "density_level": density_level,
                "trend": trend,
                "timestamp": self._now_iso(),
            }
            zone_analysis[zone_id] = zone_result

            # Track critical/high zones for alerts
            if density_level == "CRITICAL":
                critical_zones.append(zone_id)
            elif density_level == "HIGH":
                high_density_zones.append(zone_id)

        # Build summary
        summary = {
            "total_people": total_people,
            "zones_analyzed": len(zone_analysis),
            "critical_zones": critical_zones,
            "high_density_zones": high_density_zones,
        }

        # Generate alert messages for critical zones
        messages: list[dict[str, Any]] = []
        if critical_zones:
            messages.append(
                self._create_message(
                    message_type=MessageType.ALERT,
                    payload={
                        "alert_type": "critical_density",
                        "zones": critical_zones,
                        "details": {
                            z: zone_analysis[z] for z in critical_zones
                        },
                    },
                    priority=MessagePriority.CRITICAL,
                    description=f"CRITICAL density in zones: {', '.join(critical_zones)}",
                )
            )

        # Standard crowd update message
        messages.append(
            self._create_message(
                message_type=MessageType.CROWD_UPDATE,
                payload=summary,
                priority=MessagePriority.MEDIUM,
                description=f"Crowd analysis complete: {total_people} total people across {len(zone_analysis)} zones",
            )
        )

        self._log_action(
            "completed",
            f"{total_people} people, {len(critical_zones)} critical zones",
        )

        return {
            "crowd_analysis": {
                "zones": zone_analysis,
                "summary": summary,
                "timestamp": self._now_iso(),
            },
            "messages": messages,
        }
