"""
Fallback Simulator — Complete self-contained demo simulator.

Runs the full evacuation simulation loop without any external
dependencies (no SUMO, no OSRM, no GPU, no database).
"""

from __future__ import annotations

import logging
from typing import Any

from simulation.crowd_simulator import CrowdSimulator
from simulation.traffic_simulator import TrafficSimulator
from simulation.evacuation_simulator import EvacuationSimulator
from simulation.scenario_manager import ScenarioManager

logger = logging.getLogger(__name__)


class FallbackSimulator:
    """Complete self-contained evacuation simulator for demo mode.

    Combines crowd, traffic, and evacuation simulators with the
    agent workflow for a full end-to-end simulation.
    """

    def __init__(self) -> None:
        self.scenario_manager = ScenarioManager()
        self.crowd_sim = CrowdSimulator()
        self.traffic_sim = TrafficSimulator()
        self.evac_sim = EvacuationSimulator()
        self._state_data: dict[str, Any] = {}
        self._running = False
        self._current_step = 0

    def initialize(self, scenario_name: str = "default_demo") -> dict[str, Any]:
        """Initialize the simulation with a scenario.

        Returns:
            Initial state data.
        """
        self._state_data = self.scenario_manager.get_scenario_state_data(scenario_name)
        self.evac_sim.initialize(self._state_data["zones"])
        self._running = True
        self._current_step = 0
        logger.info("Fallback simulator initialized with scenario '%s'", scenario_name)
        return self._state_data

    def step(self, assignments: dict[str, list[dict]] | None = None) -> dict[str, Any]:
        """Run one simulation step.

        Args:
            assignments: Current evacuation assignments.

        Returns:
            Step result with updated state.
        """
        if not self._running:
            return {"error": "Simulator not running"}

        self._current_step += 1
        assigns = assignments or {}

        # Apply scenario events
        events = self.scenario_manager.get_events_for_step(
            self._state_data.get("scenario_name", "default_demo"),
            self._current_step,
        )
        for event in events:
            self._apply_event(event)

        # Simulate crowd movement
        self._state_data["zones"] = self.crowd_sim.simulate_step(
            self._state_data["zones"], assigns
        )

        # Simulate traffic changes
        self._state_data["roads"] = self.traffic_sim.simulate_step(
            self._state_data["roads"], assigns
        )

        # Record progress
        snapshot = self.evac_sim.record_step(
            self._state_data["zones"], self._state_data["roads"]
        )

        # Check completion
        if self.evac_sim.is_complete():
            self._running = False
            logger.info("Evacuation complete at step %d", self._current_step)

        return {
            "step": self._current_step,
            "snapshot": snapshot,
            "events_triggered": events,
            "is_complete": not self._running,
            "zones": self._state_data["zones"],
            "roads": self._state_data["roads"],
        }

    def _apply_event(self, event: dict[str, Any]) -> None:
        """Apply a scenario event."""
        etype = event.get("type", "")
        data = event.get("data", {})
        logger.info("Event at step %d: %s — %s", self._current_step, etype, event.get("description", ""))

        if etype == "road_blocked":
            rid = data.get("road_id", "")
            self._state_data["roads"] = self.traffic_sim.block_road(self._state_data["roads"], rid)
        elif etype == "road_cleared":
            rid = data.get("road_id", "")
            cong = data.get("new_congestion", 0.5)
            self._state_data["roads"] = self.traffic_sim.unblock_road(self._state_data["roads"], rid, cong)
        elif etype == "congestion_increase":
            rid = data.get("road_id", "")
            if rid in self._state_data["roads"]:
                self._state_data["roads"][rid]["congestion"] = data.get("new_congestion", 0.8)
        elif etype == "crowd_surge":
            zid = data.get("zone_id", "")
            new_count = data.get("new_crowd_count", 0)
            if zid in self._state_data["zones"]:
                self._state_data["zones"][zid]["crowd_count"] = new_count

    def get_state(self) -> dict[str, Any]:
        return dict(self._state_data)

    def get_summary(self) -> dict[str, Any]:
        return self.evac_sim.get_summary()

    @property
    def is_running(self) -> bool:
        return self._running
