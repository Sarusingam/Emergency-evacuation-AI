"""
Crowd Simulator — Simulates crowd generation, movement, evacuation.
"""

from __future__ import annotations

import logging
import random
from typing import Any

logger = logging.getLogger(__name__)


class CrowdSimulator:
    """Simulates crowd behavior during evacuation."""

    def __init__(self, walking_speed: float = 1.2, density_speed_factor: float = 0.5) -> None:
        self.walking_speed = walking_speed
        self.density_speed_factor = density_speed_factor

    def simulate_step(
        self,
        zones: dict[str, dict[str, Any]],
        assignments: dict[str, list[dict[str, Any]]],
        time_step: float = 1.0,
    ) -> dict[str, dict[str, Any]]:
        """Simulate one time step of crowd movement.

        People move from zones toward exits based on assignments.

        Args:
            zones: Current zone data with crowd_count.
            assignments: Zone-to-exit assignments with people counts.
            time_step: Simulation time step in seconds.

        Returns:
            Updated zone data with new crowd counts.
        """
        # Calculate total assigned across all zones
        has_any_assignments = any(
            len(assigns) > 0 for assigns in assignments.values()
        ) if assignments else False

        updated = {}
        for zid, zdata in zones.items():
            crowd = zdata.get("crowd_count", 0)
            zone_assigns = assignments.get(zid, [])

            # Calculate evacuation rate
            total_assigned = sum(a.get("people", 0) for a in zone_assigns)

            if crowd > 0 and (total_assigned > 0 or has_any_assignments):
                # People leave at walking speed, adjusted by density
                area = zdata.get("area", 10000)
                density = crowd / max(area, 1)
                speed_factor = max(0.3, 1.0 - density * self.density_speed_factor)

                if total_assigned > 0:
                    # Assigned zones evacuate faster
                    evac_fraction = min(0.05, total_assigned / max(crowd, 1) * 0.1)
                    evacuation_rate = max(5, int(crowd * evac_fraction * speed_factor * time_step))
                else:
                    # Unassigned zones still have some natural evacuation
                    evacuation_rate = max(1, int(crowd * 0.008 * speed_factor * time_step))

                crowd = max(0, crowd - evacuation_rate)

            updated[zid] = {**zdata, "crowd_count": crowd}

        return updated

    def add_crowd_surge(
        self, zones: dict[str, dict[str, Any]],
        zone_id: str, additional: int,
    ) -> dict[str, dict[str, Any]]:
        """Simulate a crowd surge in a zone."""
        if zone_id in zones:
            zones[zone_id]["crowd_count"] = zones[zone_id].get("crowd_count", 0) + additional
        return zones
