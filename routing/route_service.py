"""
Route Service — High-level routing facade.

Provides a unified interface for routing that selects between
OSRM (real roads) and NetworkX (graph-based) automatically.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from routing.graph_builder import build_graph_from_scenario
from routing.osrm_client import OSRMClient

logger = logging.getLogger(__name__)


class RouteService:
    """High-level routing service.

    Automatically selects the best available routing backend:
    1. OSRM (if available and configured)
    2. NetworkX graph (always available)
    """

    def __init__(
        self,
        use_osrm: bool = False,
        osrm_url: str = "http://localhost:5000",
    ) -> None:
        """Initialize the route service.

        Args:
            use_osrm: Whether to attempt OSRM routing.
            osrm_url: OSRM server URL.
        """
        self.use_osrm = use_osrm
        self._osrm = OSRMClient(osrm_url) if use_osrm else None
        self._graph: nx.DiGraph | None = None

    def initialize_graph(
        self,
        roads: dict[str, dict[str, Any]],
        zones: dict[str, dict[str, Any]] | None = None,
        exits: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Build the routing graph from scenario data.

        Args:
            roads: Road data.
            zones: Zone data.
            exits: Exit data.
        """
        self._graph = build_graph_from_scenario(roads, zones, exits)

    def get_graph(self) -> nx.DiGraph | None:
        """Get the current routing graph.

        Returns:
            The NetworkX graph, or None if not initialized.
        """
        return self._graph

    def find_route(
        self,
        origin: str,
        destination: str,
        cost_weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Find the best route between two nodes.

        Args:
            origin: Source node ID.
            destination: Target node ID.
            cost_weights: Cost function weights.

        Returns:
            Route dict with path, cost, travel_time, distance, feasible.
        """
        if self._graph is None:
            return {
                "path": [],
                "cost": float("inf"),
                "feasible": False,
                "reason": "Graph not initialized",
            }

        from agents.tools import find_shortest_path
        return find_shortest_path(
            self._graph, origin, destination, cost_weights
        )

    def update_road(
        self,
        road_id: str,
        updates: dict[str, Any],
    ) -> None:
        """Update road attributes in the graph.

        Args:
            road_id: Road identifier.
            updates: Dict of attributes to update.
        """
        if self._graph is None:
            return

        for u, v, data in self._graph.edges(data=True):
            if data.get("road_id") == road_id:
                data.update(updates)
