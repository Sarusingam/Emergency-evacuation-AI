"""
Evacuation Simulator — Tracks overall evacuation progress.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class EvacuationSimulator:
    """Tracks overall evacuation progress and statistics."""

    def __init__(self) -> None:
        self.start_time: str | None = None
        self.step_count = 0
        self.history: list[dict[str, Any]] = []
        self.initial_population = 0

    def initialize(self, zones: dict[str, dict[str, Any]]) -> None:
        """Initialize with current zone populations."""
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.step_count = 0
        self.initial_population = sum(z.get("crowd_count", 0) for z in zones.values())
        self.history = []

    def record_step(self, zones: dict[str, dict[str, Any]], roads: dict[str, dict] | None = None) -> dict[str, Any]:
        """Record one simulation step."""
        self.step_count += 1
        current_pop = sum(z.get("crowd_count", 0) for z in zones.values())
        evacuated = self.initial_population - current_pop
        progress = evacuated / max(self.initial_population, 1)
        blocked_roads = sum(1 for r in (roads or {}).values() if r.get("blocked", False))

        snapshot = {
            "step": self.step_count,
            "current_population": current_pop,
            "evacuated": evacuated,
            "progress": round(progress, 4),
            "blocked_roads": blocked_roads,
            "zones": {zid: z.get("crowd_count", 0) for zid, z in zones.items()},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.history.append(snapshot)
        return snapshot

    def is_complete(self, threshold: float = 0.95) -> bool:
        """Check if evacuation is sufficiently complete."""
        if not self.history:
            return False
        return self.history[-1].get("progress", 0) >= threshold

    def get_summary(self) -> dict[str, Any]:
        """Get evacuation summary statistics."""
        latest = self.history[-1] if self.history else {}
        return {
            "start_time": self.start_time,
            "steps_completed": self.step_count,
            "initial_population": self.initial_population,
            "current_population": latest.get("current_population", self.initial_population),
            "evacuated": latest.get("evacuated", 0),
            "progress": latest.get("progress", 0),
            "is_complete": self.is_complete(),
        }
