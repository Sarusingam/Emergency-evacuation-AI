"""
Scenario Manager — Loads and manages evacuation scenarios from YAML.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


class ScenarioManager:
    """Manages evacuation scenario loading and lifecycle."""

    def __init__(self, scenarios_path: str | Path | None = None) -> None:
        self.scenarios_path = Path(scenarios_path) if scenarios_path else CONFIG_DIR / "scenarios.yaml"
        self._scenarios: dict[str, Any] = {}
        self._active_scenario: str | None = None

    def load_scenarios(self) -> dict[str, Any]:
        """Load all scenarios from YAML file."""
        if not self.scenarios_path.exists():
            logger.warning("Scenarios file not found: %s", self.scenarios_path)
            return {}
        with open(self.scenarios_path, "r") as f:
            self._scenarios = yaml.safe_load(f) or {}
        logger.info("Loaded %d scenarios", len(self._scenarios))
        return self._scenarios

    def get_scenario(self, name: str = "default_demo") -> dict[str, Any]:
        """Get a specific scenario by name."""
        if not self._scenarios:
            self.load_scenarios()
        scenario = self._scenarios.get(name)
        if not scenario:
            available = list(self._scenarios.keys())
            raise ValueError(f"Scenario '{name}' not found. Available: {available}")
        return scenario

    def get_scenario_state_data(self, name: str = "default_demo") -> dict[str, Any]:
        """Convert a scenario into data suitable for EvacuationState.

        Returns dict with zones, roads, exits, vehicles as dicts keyed by ID.
        """
        scenario = self.get_scenario(name)

        zones = {}
        for z in scenario.get("zones", []):
            zid = z["id"]
            zones[zid] = {
                "id": zid, "name": z.get("name", zid),
                "center_lat": z.get("center", {}).get("lat", 0),
                "center_lon": z.get("center", {}).get("lon", 0),
                "radius": z.get("radius", 200),
                "crowd_count": z.get("initial_crowd", 0),
                "area": z.get("area", 10000),
            }

        roads = {}
        for r in scenario.get("roads", []):
            rid = r["id"]
            roads[rid] = {
                "id": rid, "name": r.get("name", rid),
                "from_node": r.get("from_node", ""),
                "to_node": r.get("to_node", ""),
                "length": r.get("length", 100),
                "travel_time": r.get("travel_time", 5.0),
                "capacity": r.get("capacity", 500),
                "congestion": r.get("initial_congestion", 0.0),
                "risk": r.get("risk", 0.0),
                "blocked": r.get("blocked", False),
            }

        exits = {}
        for e in scenario.get("exits", []):
            eid = e["id"]
            exits[eid] = {
                "id": eid, "name": e.get("name", eid),
                "lat": e.get("location", {}).get("lat", 0),
                "lon": e.get("location", {}).get("lon", 0),
                "capacity": e.get("capacity", 1000),
                "flow_rate": e.get("flow_rate", 150),
                "current_load": 0,
            }

        vehicles = {}
        for v in scenario.get("vehicles", []):
            vid = v["id"]
            vehicles[vid] = {
                "id": vid, "type": v.get("type", "bus"),
                "capacity": v.get("capacity", 50),
                "lat": v.get("location", {}).get("lat", 0),
                "lon": v.get("location", {}).get("lon", 0),
                "assigned_zone": v.get("assigned_zone"),
                "status": v.get("status", "available"),
            }

        events = scenario.get("events", [])

        return {
            "zones": zones, "roads": roads, "exits": exits,
            "vehicles": vehicles, "events": events,
            "scenario_name": name,
            "map_center": scenario.get("map_center", {"lat": 40.7128, "lon": -74.006}),
        }

    def get_events_for_step(self, name: str, step: int) -> list[dict]:
        """Get events that trigger at a specific simulation step."""
        scenario = self.get_scenario(name)
        return [e for e in scenario.get("events", []) if e.get("step") == step]
