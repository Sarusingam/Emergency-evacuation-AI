"""
Emergency Service — Core orchestration service.

Manages the emergency lifecycle: initialization, agent workflow
execution, simulation stepping, and state querying.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any

from agents.agent_state import create_initial_state
from agents.graph import create_runnable_graph
from simulation.fallback_simulator import FallbackSimulator
from simulation.scenario_manager import ScenarioManager
from communication.local_bus import LocalEventBus

logger = logging.getLogger(__name__)


class EmergencyService:
    """Central service orchestrating the evacuation system."""

    def __init__(self) -> None:
        self.scenario_manager = ScenarioManager()
        self.simulator = FallbackSimulator()
        self.event_bus = LocalEventBus()
        self._state: dict[str, Any] = {}
        self._graph = None
        self._active = False
        self._scenario_data: dict[str, Any] = {}
        self._route_version: int = 0
        self.initialize()

    def initialize(self) -> None:
        """Initialize service components and baseline scenario data."""
        try:
            self._scenario_data = self.scenario_manager.get_scenario_state_data("default_demo")
            
            # Compute baseline shortest evacuation routes using NetworkX graph
            from agents.tools import build_road_graph, find_all_zone_exit_routes
            graph = build_road_graph(self._scenario_data.get("roads", {}))
            baseline_routes = find_all_zone_exit_routes(
                graph,
                self._scenario_data.get("zones", {}),
                self._scenario_data.get("exits", {}),
            )

            self._state = {
                "zones": dict(self._scenario_data.get("zones", {})),
                "roads": dict(self._scenario_data.get("roads", {})),
                "exits": dict(self._scenario_data.get("exits", {})),
                "vehicles": dict(self._scenario_data.get("vehicles", {})),
                "evacuation_routes": {"routes": baseline_routes},
                "simulation_step": 0,
                "needs_replan": False,
            }
            self._graph = create_runnable_graph()
            logger.info("Emergency service initialized with baseline scenario data and routes")
        except Exception as e:
            logger.warning("Initialization warning: %s", e)
            self._graph = None

    def start_emergency(
        self,
        emergency_type: str = "chemical_spill",
        severity: str = "high",
        scenario: str = "default_demo",
    ) -> dict[str, Any]:
        """Start a new emergency and run the agent workflow.

        Returns:
            Emergency status with plan.
        """
        logger.info("Starting emergency: type=%s, severity=%s, scenario=%s",
                     emergency_type, severity, scenario)

        # Load scenario
        self._scenario_data = self.scenario_manager.get_scenario_state_data(scenario)

        # Initialize simulation
        self.simulator.initialize(scenario)

        # Create agent state
        self._state = create_initial_state(
            emergency_id=f"emergency_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            emergency_type=emergency_type,
            emergency_severity=severity,
            zones=self._scenario_data["zones"],
            roads=self._scenario_data["roads"],
            exits=self._scenario_data["exits"],
            vehicles=self._scenario_data["vehicles"],
        )

        # Run agent workflow
        if self._graph:
            try:
                result = self._graph.invoke(self._state)
                self._state.update(result)
            except Exception as e:
                logger.error("Agent workflow failed: %s", e)

        self._active = True
        self.event_bus.publish("emergency", {"action": "started", "state": self._get_summary()})

        return self._get_summary()

    def step_simulation(self) -> dict[str, Any]:
        """Run one simulation step and re-run agents if needed."""
        if not self._active:
            return {"error": "No active emergency"}

        # Get current assignments
        plan = self._state.get("evacuation_plan", {})
        assignments = plan.get("assignments", {})

        # Step simulation
        step_result = self.simulator.step(assignments)

        # Update state with new zone/road data
        self._state["zones"] = step_result.get("zones", self._state.get("zones", {}))
        self._state["roads"] = step_result.get("roads", self._state.get("roads", {}))
        self._state["simulation_step"] = step_result.get("step", 0)

        # Check if events triggered replanning need
        if step_result.get("events_triggered"):
            self._state["needs_replan"] = True

        # Re-run agents if needed
        if self._state.get("needs_replan", False) and self._graph:
            try:
                self._state["needs_replan"] = False
                result = self._graph.invoke(self._state)
                self._state.update(result)
                self._route_version += 1
            except Exception as e:
                logger.error("Re-plan failed: %s", e)

        if step_result.get("is_complete"):
            self._active = False

        return {
            "step": step_result.get("step", 0),
            "snapshot": step_result.get("snapshot", {}),
            "events": step_result.get("events_triggered", []),
            "is_complete": step_result.get("is_complete", False),
        }

    def get_state(self) -> dict[str, Any]:
        """Get current evacuation state."""
        return self._get_summary()

    def get_crowd_analysis(self) -> dict[str, Any]:
        return self._state.get("crowd_analysis", {})

    def get_risk_assessment(self) -> dict[str, Any]:
        return self._state.get("risk_assessment", {})

    def get_traffic_status(self) -> dict[str, Any]:
        return self._state.get("traffic_status", {})

    def get_transport_status(self) -> dict[str, Any]:
        return self._state.get("transport_status", {})

    def get_evacuation_routes(self) -> dict[str, Any]:
        return self._state.get("evacuation_routes", {})

    def get_evacuation_plan(self) -> dict[str, Any]:
        return self._state.get("evacuation_plan", {})

    def get_agent_messages(self) -> list[dict[str, Any]]:
        return self._state.get("messages", [])

    def get_zones(self) -> dict[str, Any]:
        return self._state.get("zones", {})

    def get_roads(self) -> dict[str, Any]:
        return self._state.get("roads", {})

    def get_exits(self) -> dict[str, Any]:
        return self._state.get("exits", {})

    def get_vehicles(self) -> dict[str, Any]:
        return self._state.get("vehicles", {})

    def block_road(self, road_id: str) -> dict[str, Any]:
        """Block a road and trigger replanning."""
        roads = self._state.get("roads", {})
        if road_id in roads:
            roads[road_id]["blocked"] = True
            roads[road_id]["congestion"] = 1.0
            if hasattr(self.simulator, "_state_data") and "roads" in self.simulator._state_data:
                sim_roads = self.simulator._state_data["roads"]
                if road_id in sim_roads:
                    sim_roads[road_id]["blocked"] = True
                    sim_roads[road_id]["congestion"] = 1.0
            self._state["needs_replan"] = True
            self._state["replan_reason"] = f"Road {road_id} blocked"
            self._route_version += 1
            return {"status": "blocked", "road_id": road_id}
        return {"error": f"Road {road_id} not found"}

    def update_crowd(self, zone_id: str, new_count: int) -> dict[str, Any]:
        """Update crowd count for a zone."""
        zones = self._state.get("zones", {})
        if zone_id in zones:
            zones[zone_id]["crowd_count"] = new_count
            if hasattr(self.simulator, "_state_data") and "zones" in self.simulator._state_data:
                sim_zones = self.simulator._state_data["zones"]
                if zone_id in sim_zones:
                    sim_zones[zone_id]["crowd_count"] = new_count
            return {"status": "updated", "zone_id": zone_id, "count": new_count}
        return {"error": f"Zone {zone_id} not found"}

    @property
    def is_active(self) -> bool:
        return self._active

    def _get_summary(self) -> dict[str, Any]:
        plan = self._state.get("evacuation_plan", {})
        sim_summary = self.simulator.get_summary()
        return {
            "emergency_id": self._state.get("emergency_id", ""),
            "emergency_type": self._state.get("emergency_type", ""),
            "severity": self._state.get("emergency_severity", ""),
            "status": "active" if self._active else "inactive",
            "simulation_step": self._state.get("simulation_step", 0),
            "total_people": plan.get("total_people", 0),
            "people_assigned": plan.get("people_assigned", 0),
            "progress": sim_summary.get("progress", 0),
            "evacuated": sim_summary.get("evacuated", 0),
            "plan_status": plan.get("status", "none"),
            "reasoning": self._state.get("coordinator_reasoning", ""),
            "replan_count": self._state.get("replan_count", 0),
            "map_center": self._scenario_data.get("map_center", {}),
        }

    # ── User / Evacuee helpers ──────────────────────────────────

    @property
    def route_version(self) -> int:
        """Current route version counter for change detection."""
        return self._route_version

    def get_user_route(self, zone_id: str) -> dict[str, Any]:
        """Get personalized evacuation instructions for a zone.

        Derives all data from the existing AI-generated evacuation plan.
        Returns only evacuee-safe information.

        Args:
            zone_id: The zone the evacuee is in.

        Returns:
            Dict with destination, route steps, ETA, risk level, etc.
        """
        zones = self._state.get("zones", {})
        if not zones:
            zones = self._scenario_data.get("zones", {})

        if zone_id not in zones:
            return {
                "emergency_active": self._active,
                "error": f"Unknown zone: {zone_id}",
                "message": "Could not determine your zone. Select your location manually.",
            }

        zone_data = zones[zone_id]
        zone_name = zone_data.get("name", zone_id)

        # Get risk level
        risk_assessment = self._state.get("risk_assessment", {})
        zone_risk = risk_assessment.get("zones", {}).get(zone_id, {})
        risk_level = zone_risk.get("risk_level", "LOW" if not self._active else "UNKNOWN")

        # Get evacuation plan assignments for this zone
        plan = self._state.get("evacuation_plan", {})
        assignments = plan.get("assignments", {})
        zone_assignments = assignments.get(zone_id, [])

        # Get all routes for this zone
        evac_routes = self._state.get("evacuation_routes", {})
        zone_routes = evac_routes.get("routes", {}).get(zone_id, [])
        if not zone_routes and zone_id in evac_routes and isinstance(evac_routes[zone_id], list):
            zone_routes = evac_routes[zone_id]

        # Find the best assignment (most people assigned = primary route)
        best_assignment = None
        if zone_assignments:
            best_assignment = max(zone_assignments, key=lambda a: a.get("people", 0))

        # Get exits and roads data
        exits = self._state.get("exits", {}) or self._scenario_data.get("exits", {})
        roads = self._state.get("roads", {}) or self._scenario_data.get("roads", {})

        # Resolve destination and route path
        destination_exit_id = ""
        destination_exit_name = ""
        eta_minutes = 0.0
        route_path = []

        if best_assignment:
            destination_exit_id = best_assignment.get("exit_id", "")
            eta_minutes = best_assignment.get("travel_time", 0.0)
            route_path = best_assignment.get("route", []) or best_assignment.get("path", [])

        # Fallback to shortest feasible route from zone_routes or direct graph
        if not destination_exit_id or not route_path:
            feasible = [r for r in zone_routes if r.get("feasible", False)]
            if feasible:
                best_r = min(feasible, key=lambda r: r.get("total_time", r.get("travel_time", float("inf"))))
                destination_exit_id = best_r.get("exit_id", "")
                eta_minutes = best_r.get("total_time", best_r.get("travel_time", 0.0))
                route_path = best_r.get("path", []) or best_r.get("route", [])

        if destination_exit_id:
            exit_data = exits.get(destination_exit_id, {})
            destination_exit_name = exit_data.get("name", destination_exit_id)

        # Convert path nodes to route steps with road names
        route_steps = []
        if route_path and len(route_path) >= 2:
            for i in range(len(route_path) - 1):
                from_node = route_path[i]
                to_node = route_path[i + 1]
                for road_id, road_data in roads.items():
                    r_from = road_data.get("from_node", "")
                    r_to = road_data.get("to_node", "")
                    if (r_from == from_node and r_to == to_node) or \
                       (r_to == from_node and r_from == to_node):
                        route_steps.append({
                            "road_id": road_id,
                            "road_name": road_data.get("name", road_id),
                            "blocked": road_data.get("blocked", False),
                        })
                        break

        # Build human-readable summary
        if route_steps:
            step_names = [
                s["road_name"].split(" - ")[0] if " - " in s["road_name"] else s["road_name"]
                for s in route_steps
            ]
            route_summary = f"Proceed via {' -> '.join(step_names)} to {destination_exit_name}"
        elif destination_exit_name:
            route_summary = f"Proceed directly to {destination_exit_name}"
        else:
            route_summary = "Designated evacuation corridor available upon emergency activation."

        # Blocked roads affecting the scenario
        all_blocked = [
            road_data.get("name", road_id)
            for road_id, road_data in roads.items()
            if road_data.get("blocked", False)
        ]

        return {
            "emergency_active": self._active,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "risk_level": risk_level,
            "destination_exit_id": destination_exit_id,
            "destination_exit_name": destination_exit_name,
            "route_steps": route_steps,
            "route_summary": route_summary,
            "eta_minutes": round(eta_minutes, 1),
            "roads_to_avoid": all_blocked if self._active else [],
            "route_version": self._route_version,
            "last_updated": self._state.get("last_updated", ""),
            "message": route_summary if self._active else "STANDBY — No active emergency order.",
            "mode": "demo",
        }

    def get_user_alerts(self) -> list[dict[str, Any]]:
        """Get active alerts relevant to evacuees.

        Returns only active alerts when emergency is in progress.
        Returns empty list in STANDBY mode.
        """
        if not self._active:
            return []

        alerts: list[dict[str, Any]] = []

        # Blocked roads
        roads = self._state.get("roads", {})
        for road_id, road_data in roads.items():
            if road_data.get("blocked", False):
                road_name = road_data.get("name", road_id)
                alerts.append({
                    "alert_type": "road_blocked",
                    "message": f"{road_name} is BLOCKED. Avoid this corridor.",
                    "severity": "critical",
                    "timestamp": self._state.get("last_updated", ""),
                })

        # High congestion roads
        for road_id, road_data in roads.items():
            congestion = road_data.get("congestion", 0)
            if congestion > 0.7 and not road_data.get("blocked", False):
                road_name = road_data.get("name", road_id)
                alerts.append({
                    "alert_type": "high_congestion",
                    "message": f"{road_name} has heavy congestion. Expect delays.",
                    "severity": "warning",
                    "timestamp": self._state.get("last_updated", ""),
                })

        # Critical risk zones
        risk = self._state.get("risk_assessment", {})
        for zone_id, zone_risk in risk.get("zones", {}).items():
            if zone_risk.get("risk_level") == "CRITICAL":
                zone_name = self._state.get("zones", {}).get(zone_id, {}).get("name", zone_id)
                alerts.append({
                    "alert_type": "critical_risk",
                    "message": f"{zone_name} is at CRITICAL hazard risk. Evacuate immediately.",
                    "severity": "critical",
                    "timestamp": zone_risk.get("timestamp", ""),
                })

        return alerts

    def resolve_location(self, lat: float, lon: float) -> dict[str, Any]:
        """Resolve GPS coordinates to the nearest evacuation zone.

        Uses Haversine formula to compute distance from the given
        coordinates to each zone center.

        Args:
            lat: Latitude from browser geolocation.
            lon: Longitude from browser geolocation.

        Returns:
            Dict with resolved zone_id, zone_name, distance.
        """
        zones = self._state.get("zones", {})
        if not zones:
            # Fall back to scenario data
            zones = self._scenario_data.get("zones", {})

        if not zones:
            return {
                "zone_id": "",
                "zone_name": "",
                "distance_meters": 0,
                "message": "No zone data available. Select your zone manually.",
            }

        best_zone = ""
        best_name = ""
        best_dist = float("inf")

        for zone_id, zone_data in zones.items():
            z_lat = zone_data.get("center_lat", 0)
            z_lon = zone_data.get("center_lon", 0)
            dist = self._haversine(lat, lon, z_lat, z_lon)
            if dist < best_dist:
                best_dist = dist
                best_zone = zone_id
                best_name = zone_data.get("name", zone_id)

        return {
            "zone_id": best_zone,
            "zone_name": best_name,
            "distance_meters": round(best_dist, 1),
            "message": f"Nearest zone: {best_name} ({best_dist:.0f}m away)",
        }

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compute Haversine distance in meters between two lat/lon points."""
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _node_coords(self, node_id: str) -> tuple[float, float] | None:
        """Resolve a node ID (zone or exit) to (lat, lon)."""
        zones = self._state.get("zones", {})
        exits = self._state.get("exits", {})
        if node_id in zones:
            z = zones[node_id]
            return (z.get("center_lat", 0), z.get("center_lon", 0))
        if node_id in exits:
            e = exits[node_id]
            return (e.get("lat", 0), e.get("lon", 0))
        return None

    def get_user_map_data(self, zone_id: str) -> dict[str, Any]:
        """Return all map data needed for the user view (Demo & Real modes).

        Provides:
        - map_mode: "demo" or "real"
        - all_zones, all_exits with both lat/lon and grid (x, y) coordinates
        - all_roads: full topology with from_node, to_node, blocked, congestion
        - route_nodes & route_roads: exact path node/road IDs from AI plan
        - route_coords: lat/lon polyline for Leaflet GIS view
        - blocked_segments & congested_segments

        Args:
            zone_id: The user's selected zone.

        Returns:
            Dict containing map topology, user route, and status.
        """
        map_center = self._scenario_data.get("map_center", {"lat": 17.4100, "lon": 78.4700})

        zones = self._state.get("zones", {})
        exits = self._state.get("exits", {})
        roads = self._state.get("roads", {})

        # Grid positions for Hyderabad demo scenario layout
        GRID_POS = {
            "zone_z1": {"x": 180, "y": 150},  # Z1 - Miyapur (North-West)
            "zone_z2": {"x": 180, "y": 300},  # Z2 - Raidurg (West)
            "zone_z6": {"x": 450, "y": 150},  # Z6 - JBS (North-Central)
            "zone_z5": {"x": 450, "y": 380},  # Z5 - MGBS (Central)
            "zone_z3": {"x": 720, "y": 260},  # Z3 - Nagole (East)
            "zone_z4": {"x": 720, "y": 380},  # Z4 - LB Nagar (South-East)
            "exit_north": {"x": 450, "y": 40},   # North Evacuation Point (Medchal)
            "exit_east": {"x": 840, "y": 260},   # East Evacuation Point (Ghatkesar)
            "exit_south": {"x": 580, "y": 520},  # South Evacuation Point (Shamshabad)
            "exit_west": {"x": 60, "y": 150},    # West Evacuation Point (Patancheru)
        }

        # All zone markers
        all_zones = []
        for zid, zdata in zones.items():
            pos = GRID_POS.get(zid, {"x": 400, "y": 250})
            all_zones.append({
                "id": zid,
                "name": zdata.get("name", zid),
                "lat": zdata.get("center_lat", 0),
                "lon": zdata.get("center_lon", 0),
                "grid_x": pos["x"],
                "grid_y": pos["y"],
                "crowd_count": zdata.get("crowd_count", 0),
                "is_user_zone": zid == zone_id,
            })

        # All exit markers
        all_exits = []
        for eid, edata in exits.items():
            pos = GRID_POS.get(eid, {"x": 400, "y": 250})
            all_exits.append({
                "id": eid,
                "name": edata.get("name", eid),
                "lat": edata.get("lat", 0),
                "lon": edata.get("lon", 0),
                "grid_x": pos["x"],
                "grid_y": pos["y"],
                "capacity": edata.get("capacity", 1000),
            })

        # All roads topology
        all_roads = []
        for road_id, road_data in roads.items():
            from_node = road_data.get("from_node", "")
            to_node = road_data.get("to_node", "")
            all_roads.append({
                "id": road_id,
                "name": road_data.get("name", road_id),
                "from_node": from_node,
                "to_node": to_node,
                "blocked": road_data.get("blocked", False),
                "congestion": round(road_data.get("congestion", 0.0), 2),
                "risk": round(road_data.get("risk", 0.0), 2),
                "travel_time": round(road_data.get("travel_time", 0.0), 1),
                "length": road_data.get("length", 100),
                "from_grid": GRID_POS.get(from_node, {"x": 0, "y": 0}),
                "to_grid": GRID_POS.get(to_node, {"x": 0, "y": 0}),
            })

        # Blocked road segments (only when emergency active)
        blocked_segments = []
        if self._active:
            for road_id, road_data in roads.items():
                if road_data.get("blocked", False):
                    from_coords = self._node_coords(road_data.get("from_node", ""))
                    to_coords = self._node_coords(road_data.get("to_node", ""))
                    if from_coords and to_coords:
                        blocked_segments.append({
                            "road_id": road_id,
                            "name": road_data.get("name", road_id),
                            "coords": [list(from_coords), list(to_coords)],
                        })

        # High-congestion road segments (only when emergency active)
        congested_segments = []
        if self._active:
            for road_id, road_data in roads.items():
                cong = road_data.get("congestion", 0)
                if cong > 0.6 and not road_data.get("blocked", False):
                    from_coords = self._node_coords(road_data.get("from_node", ""))
                    to_coords = self._node_coords(road_data.get("to_node", ""))
                    if from_coords and to_coords:
                        congested_segments.append({
                            "road_id": road_id,
                            "name": road_data.get("name", road_id),
                            "congestion": round(cong, 2),
                            "coords": [list(from_coords), list(to_coords)],
                        })

        # Risk zones (only when emergency active)
        risk_zones = []
        if self._active:
            risk_assessment = self._state.get("risk_assessment", {})
            for zid, zrisk in risk_assessment.get("zones", {}).items():
                level = zrisk.get("risk_level", "LOW")
                if level in ("HIGH", "CRITICAL"):
                    zdata = zones.get(zid, {})
                    pos = GRID_POS.get(zid, {"x": 450, "y": 300})
                    risk_zones.append({
                        "id": zid,
                        "name": zdata.get("name", zid),
                        "risk_level": level,
                        "lat": zdata.get("center_lat", 0),
                        "lon": zdata.get("center_lon", 0),
                        "grid_x": pos["x"],
                        "grid_y": pos["y"],
                        "radius": zdata.get("radius", 300),
                    })

        # Route geometry for the user's assigned evacuation corridor
        route_coords = []
        route_nodes = []
        route_roads = []
        destination = None

        if zone_id:
            route_info = self.get_user_route(zone_id)
            dest_id = route_info.get("destination_exit_id", "")
            route_steps = route_info.get("route_steps", [])
            route_roads = [s["road_id"] for s in route_steps]

            # Reconstruct node sequence
            if route_steps:
                nodes_seq = [zone_id]
                for s in route_steps:
                    rid = s.get("road_id", "")
                    rdata = roads.get(rid, {})
                    fn = rdata.get("from_node", "")
                    tn = rdata.get("to_node", "")
                    curr = nodes_seq[-1]
                    next_n = tn if fn == curr else fn
                    nodes_seq.append(next_n)
                route_nodes = nodes_seq
            elif dest_id:
                route_nodes = [zone_id, dest_id]

            # Destination object
            if dest_id:
                if dest_id in exits:
                    edata = exits[dest_id]
                    pos = GRID_POS.get(dest_id, {"x": 450, "y": 40})
                    destination = {
                        "id": dest_id,
                        "name": edata.get("name", dest_id),
                        "type": "exit",
                        "lat": edata.get("lat", 0),
                        "lon": edata.get("lon", 0),
                        "grid_x": pos["x"],
                        "grid_y": pos["y"],
                    }
                elif dest_id in zones:
                    zd = zones[dest_id]
                    pos = GRID_POS.get(dest_id, {"x": 450, "y": 300})
                    destination = {
                        "id": dest_id,
                        "name": zd.get("name", dest_id),
                        "type": "zone",
                        "lat": zd.get("center_lat", 0),
                        "lon": zd.get("center_lon", 0),
                        "grid_x": pos["x"],
                        "grid_y": pos["y"],
                    }

            # Lat/Lon coordinates for polyline
            for nid in route_nodes:
                c = self._node_coords(nid)
                if c:
                    route_coords.append(list(c))

            # Fallback direct line if needed
            if len(route_coords) < 2 and dest_id:
                zc = self._node_coords(zone_id)
                dc = self._node_coords(dest_id)
                if zc and dc:
                    route_coords = [list(zc), list(dc)]

        # User zone info
        user_zone = None
        if zone_id and zone_id in zones:
            zd = zones[zone_id]
            pos = GRID_POS.get(zone_id, {"x": 180, "y": 150})
            user_zone = {
                "id": zone_id,
                "name": zd.get("name", zone_id),
                "lat": zd.get("center_lat", 0),
                "lon": zd.get("center_lon", 0),
                "grid_x": pos["x"],
                "grid_y": pos["y"],
            }

        return {
            "map_mode": "demo",
            "map_center": map_center,
            "user_zone": user_zone,
            "destination": destination,
            "route_nodes": route_nodes,
            "route_roads": route_roads,
            "route_coords": route_coords,
            "all_roads": all_roads,
            "blocked_segments": blocked_segments,
            "congested_segments": congested_segments,
            "risk_zones": risk_zones,
            "all_zones": all_zones,
            "all_exits": all_exits,
            "route_version": self._route_version,
            "emergency_active": self._active,
        }


# Singleton instance
emergency_service = EmergencyService()
