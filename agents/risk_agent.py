"""
Risk Agent — Zone Risk Assessment.

This agent computes a risk score and risk level (LOW/MEDIUM/HIGH/CRITICAL)
for each zone based on multiple factors:
- Crowd density (from crowd_analysis)
- Emergency proximity (estimated from emergency type and affected zone)
- Road congestion near the zone
- Blocked exit ratio
- Structural risk

Input: state['zones'], state['crowd_analysis'], state['roads'], state['exits'].
Output: state['risk_assessment'] with per-zone risk scores and levels.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.agent_messages import MessagePriority, MessageType
from agents.tools import calculate_zone_risk_score

logger = logging.getLogger(__name__)

# Emergency type risk multipliers
EMERGENCY_TYPE_RISK = {
    "chemical_spill": 0.9,
    "fire": 0.85,
    "earthquake": 0.95,
    "flood": 0.7,
    "bomb_threat": 0.8,
    "active_shooter": 0.95,
    "general": 0.5,
}


class RiskAgent(BaseAgent):
    """Agent responsible for zone-level risk assessment.

    Combines crowd density, emergency proximity, road conditions,
    and structural factors into a composite risk score for each zone.
    Zones exceeding risk thresholds generate alert messages.
    """

    def __init__(self) -> None:
        """Initialize the Risk Agent."""
        super().__init__(
            name="risk_agent",
            description="Assesses risk levels across all zones",
        )

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Assess risk for all zones.

        Steps:
            1. Gather crowd density from crowd_analysis.
            2. Estimate emergency proximity per zone.
            3. Calculate average road congestion near each zone.
            4. Determine blocked exit ratio per zone.
            5. Compute composite risk score.
            6. Generate alerts for high/critical risk zones.

        Args:
            state: The full EvacuationState dict.

        Returns:
            State update with 'risk_assessment' and alert messages.
        """
        self._log_action("processing", "Assessing risk across all zones")

        zones = state.get("zones", {})
        roads = state.get("roads", {})
        exits = state.get("exits", {})
        crowd_analysis = state.get("crowd_analysis", {})
        emergency_type = state.get("emergency_type", "general")

        if not zones:
            self._log_warning("no zones", "No zone data for risk assessment")
            return {
                "risk_assessment": {"zones": {}, "summary": {}},
                "messages": [
                    self._create_message(
                        message_type=MessageType.RISK_UPDATE,
                        description="No zone data for risk assessment",
                        priority=MessagePriority.LOW,
                    )
                ],
            }

        zone_risks: dict[str, dict[str, Any]] = {}
        messages: list[dict[str, Any]] = []
        critical_zones: list[str] = []
        high_risk_zones: list[str] = []

        for zone_id, zone_data in zones.items():
            # 1. Crowd density (from crowd analysis or raw count)
            crowd_zones = crowd_analysis.get("zones", {})
            crowd_info = crowd_zones.get(zone_id, {})
            density = crowd_info.get("density", 0.0)
            # Normalize density to 0-1 scale (3.0 people/m² = 1.0)
            crowd_density_norm = min(density / 3.0, 1.0)

            # 2. Emergency proximity
            emergency_proximity = self._estimate_emergency_proximity(
                zone_id, zone_data, emergency_type, state
            )

            # 3. Nearby road congestion
            nearby_congestion = self._get_nearby_road_congestion(
                zone_id, roads
            )

            # 4. Blocked exit ratio
            blocked_ratio = self._get_blocked_exit_ratio(
                zone_id, roads, exits
            )

            # 5. Structural risk (base value, could be from external data)
            structural_risk = 0.1  # Default low structural risk

            # 6. Compute composite risk
            risk_score, risk_level = calculate_zone_risk_score(
                zone=zone_data,
                crowd_density=crowd_density_norm,
                nearby_road_congestion=nearby_congestion,
                blocked_exit_ratio=blocked_ratio,
                emergency_proximity=emergency_proximity,
                structural_risk=structural_risk,
            )

            zone_risks[zone_id] = {
                "zone_id": zone_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "factors": {
                    "crowd_density": round(crowd_density_norm, 3),
                    "emergency_proximity": round(emergency_proximity, 3),
                    "road_congestion": round(nearby_congestion, 3),
                    "blocked_exit_ratio": round(blocked_ratio, 3),
                    "structural_risk": round(structural_risk, 3),
                },
                "timestamp": self._now_iso(),
            }

            if risk_level == "CRITICAL":
                critical_zones.append(zone_id)
            elif risk_level == "HIGH":
                high_risk_zones.append(zone_id)

        # Generate alerts
        if critical_zones:
            messages.append(
                self._create_message(
                    message_type=MessageType.ALERT,
                    payload={
                        "alert_type": "critical_risk",
                        "zones": critical_zones,
                        "details": {
                            z: zone_risks[z] for z in critical_zones
                        },
                    },
                    priority=MessagePriority.CRITICAL,
                    description=f"CRITICAL risk in zones: {', '.join(critical_zones)}",
                )
            )

        # Standard risk update
        messages.append(
            self._create_message(
                message_type=MessageType.RISK_UPDATE,
                payload={
                    "zones_assessed": len(zone_risks),
                    "critical_zones": critical_zones,
                    "high_risk_zones": high_risk_zones,
                },
                priority=MessagePriority.MEDIUM,
                description=f"Risk assessment: {len(critical_zones)} critical, {len(high_risk_zones)} high-risk zones",
            )
        )

        self._log_action(
            "completed",
            f"{len(critical_zones)} critical, {len(high_risk_zones)} high-risk zones",
        )

        return {
            "risk_assessment": {
                "zones": zone_risks,
                "summary": {
                    "critical_zones": critical_zones,
                    "high_risk_zones": high_risk_zones,
                    "total_assessed": len(zone_risks),
                },
                "timestamp": self._now_iso(),
            },
            "messages": messages,
        }

    def _estimate_emergency_proximity(
        self,
        zone_id: str,
        zone_data: dict[str, Any],
        emergency_type: str,
        state: dict[str, Any],
    ) -> float:
        """Estimate how close a zone is to the emergency source.

        In demo mode, this uses a simple heuristic based on the
        emergency type's affected zone from the scenario events.

        Args:
            zone_id: Current zone being assessed.
            zone_data: Zone data dict.
            emergency_type: Type of the emergency.
            state: Full state for context.

        Returns:
            Proximity score 0.0 (far) to 1.0 (epicenter).
        """
        base_risk = EMERGENCY_TYPE_RISK.get(emergency_type, 0.5)

        # In a real system, this would use geospatial distance.
        # For demo, we assign higher proximity to Zone D (typical affected zone).
        proximity_map = {
            "zone_d": 1.0,   # Epicenter
            "zone_b": 0.6,   # Adjacent
            "zone_c": 0.5,   # Adjacent
            "zone_a": 0.3,   # Far
        }

        proximity = proximity_map.get(zone_id, 0.5)
        return proximity * base_risk

    def _get_nearby_road_congestion(
        self,
        zone_id: str,
        roads: dict[str, dict[str, Any]],
    ) -> float:
        """Calculate average congestion of roads connected to a zone.

        Args:
            zone_id: Zone to check.
            roads: All road data.

        Returns:
            Average congestion (0.0-1.0) of connected roads.
        """
        congestion_values: list[float] = []
        for road_data in roads.values():
            if (road_data.get("from_node") == zone_id
                    or road_data.get("to_node") == zone_id):
                congestion_values.append(
                    road_data.get("congestion",
                                 road_data.get("initial_congestion", 0.0))
                )

        if not congestion_values:
            return 0.0
        return sum(congestion_values) / len(congestion_values)

    def _get_blocked_exit_ratio(
        self,
        zone_id: str,
        roads: dict[str, dict[str, Any]],
        exits: dict[str, dict[str, Any]],
    ) -> float:
        """Calculate the ratio of exits that are unreachable from a zone.

        An exit is considered blocked if all roads leading to it from
        this zone are blocked.

        Args:
            zone_id: Zone to check.
            roads: All road data.
            exits: All exit data.

        Returns:
            Fraction of exits that are blocked (0.0-1.0).
        """
        if not exits:
            return 0.0

        # For simplicity, check if any road from this zone to an exit is blocked
        blocked_exits = 0
        for exit_id in exits:
            has_clear_path = False
            for road_data in roads.values():
                from_n = road_data.get("from_node", "")
                to_n = road_data.get("to_node", "")
                if ((from_n == zone_id and to_n == exit_id)
                        or (to_n == zone_id and from_n == exit_id)):
                    if not road_data.get("blocked", False):
                        has_clear_path = True
                        break

            # If there are no direct roads, it's not necessarily blocked
            # (could go via another zone). Only count as blocked if there
            # are direct roads and ALL are blocked.
            direct_roads = [
                r for r in roads.values()
                if (r.get("from_node") == zone_id and r.get("to_node") == exit_id)
                or (r.get("to_node") == zone_id and r.get("from_node") == exit_id)
            ]
            if direct_roads and not has_clear_path:
                blocked_exits += 1

        return blocked_exits / max(len(exits), 1)
