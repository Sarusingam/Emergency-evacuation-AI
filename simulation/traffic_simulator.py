"""
Traffic Simulator — Simulates road congestion changes and blocking.
"""

from __future__ import annotations

import logging
import random
from typing import Any

logger = logging.getLogger(__name__)


class TrafficSimulator:
    """Simulates road traffic conditions during evacuation."""

    def __init__(self, congestion_increase_rate: float = 0.02,
                 congestion_decay_rate: float = 0.01) -> None:
        self.increase_rate = congestion_increase_rate
        self.decay_rate = congestion_decay_rate

    def simulate_step(
        self,
        roads: dict[str, dict[str, Any]],
        assignments: dict[str, list[dict[str, Any]]],
    ) -> dict[str, dict[str, Any]]:
        """Simulate one step of traffic changes.

        Congestion increases on roads being used for evacuation
        and decays on unused roads.
        """
        # Find roads in active routes
        active_roads: set[str] = set()
        for zone_assigns in assignments.values():
            for a in zone_assigns:
                route = a.get("route", [])
                for i in range(len(route) - 1):
                    for rid, rdata in roads.items():
                        fn, tn = rdata.get("from_node", ""), rdata.get("to_node", "")
                        if ((fn == route[i] and tn == route[i + 1]) or
                                (tn == route[i] and fn == route[i + 1])):
                            active_roads.add(rid)

        updated = {}
        for rid, rdata in roads.items():
            r = dict(rdata)
            if r.get("blocked", False):
                updated[rid] = r
                continue

            cong = r.get("congestion", 0.0)
            if rid in active_roads:
                cong = min(1.0, cong + self.increase_rate + random.uniform(0, 0.01))
            else:
                cong = max(0.0, cong - self.decay_rate)
            r["congestion"] = round(cong, 3)
            updated[rid] = r

        return updated

    def block_road(self, roads: dict[str, dict], road_id: str) -> dict[str, dict]:
        """Block a road."""
        if road_id in roads:
            roads[road_id]["blocked"] = True
            roads[road_id]["congestion"] = 1.0
        return roads

    def unblock_road(self, roads: dict[str, dict], road_id: str,
                     congestion: float = 0.5) -> dict[str, dict]:
        """Unblock a road with residual congestion."""
        if road_id in roads:
            roads[road_id]["blocked"] = False
            roads[road_id]["congestion"] = congestion
        return roads
