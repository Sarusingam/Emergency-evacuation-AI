"""
Route Agent — Evacuation Route Optimization.

This agent computes optimal evacuation routes from zones to exits
using deterministic algorithms (NetworkX shortest path with custom
cost function). It then runs the evacuation assignment optimizer
to distribute people across exits.

All route calculations are done by the tools module — the LLM
is NEVER used for numerical route computation.

Input: state['roads'], state['zones'], state['exits'],
       state['traffic_status'].
Output: state['evacuation_routes'] with computed routes per zone.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.agent_messages import MessagePriority, MessageType
from agents.tools import (
    build_road_graph,
    find_all_zone_exit_routes,
    optimize_evacuation_assignment,
)

logger = logging.getLogger(__name__)


class RouteAgent(BaseAgent):
    """Agent responsible for computing evacuation routes.

    Uses NetworkX and the optimization engine to find shortest
    paths and optimally distribute evacuees across exits.
    """

    def __init__(self) -> None:
        """Initialize the Route Agent."""
        super().__init__(
            name="route_agent",
            description="Computes optimal evacuation routes from zones to exits",
        )

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Compute evacuation routes for all zones.

        Steps:
            1. Build road graph from current road data.
            2. Find shortest routes from every zone to every exit.
            3. Run evacuation assignment optimizer.
            4. Package results for the coordinator.

        Args:
            state: The full EvacuationState dict.

        Returns:
            State update with 'evacuation_routes' and messages.
        """
        self._log_action("processing", "Computing evacuation routes")

        roads = state.get("roads", {})
        zones = state.get("zones", {})
        exits = state.get("exits", {})

        if not roads or not zones or not exits:
            self._log_warning(
                "missing data",
                f"roads={len(roads)}, zones={len(zones)}, exits={len(exits)}",
            )
            return {
                "evacuation_routes": {"routes": {}, "assignments": {}},
                "messages": [
                    self._create_message(
                        message_type=MessageType.ROUTE_UPDATE,
                        description="Insufficient data for route computation",
                        priority=MessagePriority.HIGH,
                    )
                ],
            }

        # 1. Build graph with current road conditions
        graph = build_road_graph(roads)
        self._log_action("graph built", f"{graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

        # 2. Find all zone-to-exit routes
        all_routes = find_all_zone_exit_routes(graph, zones, exits)
        self._log_action("routes found", f"{sum(len(r) for r in all_routes.values())} total route options")

        # 3. Optimize evacuation assignment
        assignments = optimize_evacuation_assignment(zones, exits, all_routes)

        # 4. Build route summary
        route_summary = self._build_route_summary(all_routes, assignments, zones, exits)

        # Generate messages
        messages: list[dict[str, Any]] = []

        # Check for zones with no feasible routes
        no_route_zones = [
            zone_id for zone_id, zone_routes in all_routes.items()
            if not any(r.get("feasible", False) for r in zone_routes)
        ]

        if no_route_zones:
            messages.append(
                self._create_message(
                    message_type=MessageType.ALERT,
                    payload={
                        "alert_type": "no_feasible_route",
                        "zones": no_route_zones,
                    },
                    priority=MessagePriority.CRITICAL,
                    description=f"No feasible routes for zones: {', '.join(no_route_zones)}",
                )
            )

        messages.append(
            self._create_message(
                message_type=MessageType.ROUTE_UPDATE,
                payload=route_summary,
                priority=MessagePriority.HIGH,
                description=f"Routes computed: {route_summary.get('total_routes', 0)} routes across {len(zones)} zones",
            )
        )

        self._log_action(
            "completed",
            f"{route_summary.get('total_routes', 0)} feasible routes computed",
        )

        return {
            "evacuation_routes": {
                "routes": all_routes,
                "assignments": assignments,
                "summary": route_summary,
                "timestamp": self._now_iso(),
            },
            "messages": messages,
        }

    def _build_route_summary(
        self,
        all_routes: dict[str, list[dict]],
        assignments: dict[str, list[dict]],
        zones: dict[str, dict],
        exits: dict[str, dict],
    ) -> dict[str, Any]:
        """Build a human-readable route summary.

        Args:
            all_routes: All computed routes.
            assignments: Optimized assignments.
            zones: Zone data.
            exits: Exit data.

        Returns:
            Summary dict with key statistics.
        """
        total_routes = 0
        feasible_routes = 0
        total_assigned = 0
        max_travel_time = 0.0

        for zone_routes in all_routes.values():
            for route in zone_routes:
                total_routes += 1
                if route.get("feasible", False):
                    feasible_routes += 1

        for zone_assigns in assignments.values():
            for assignment in zone_assigns:
                total_assigned += assignment.get("people", 0)
                travel_time = assignment.get("travel_time", 0.0)
                if travel_time > max_travel_time:
                    max_travel_time = travel_time

        total_people = sum(
            z.get("crowd_count", 0) for z in zones.values()
        )

        return {
            "total_routes": total_routes,
            "feasible_routes": feasible_routes,
            "total_people": total_people,
            "people_assigned": total_assigned,
            "unassigned": total_people - total_assigned,
            "max_travel_time": round(max_travel_time, 2),
            "exits_used": len({
                a["exit_id"]
                for assigns in assignments.values()
                for a in assigns
                if a.get("people", 0) > 0
            }),
        }
