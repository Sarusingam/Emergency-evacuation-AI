"""
Graph Builder — Constructs NetworkX DiGraph from road data.

Builds the road network graph from scenario/map data with
all edge attributes needed by the cost function.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


def build_graph_from_scenario(
    roads: dict[str, dict[str, Any]],
    zones: dict[str, dict[str, Any]] | None = None,
    exits: dict[str, dict[str, Any]] | None = None,
) -> nx.DiGraph:
    """Build a NetworkX DiGraph from scenario road data.

    Creates a bidirectional graph where each road becomes two
    directed edges. Node attributes include type (zone/exit)
    and geographic coordinates.

    Args:
        roads: Road data keyed by road_id.
        zones: Optional zone data for node attributes.
        exits: Optional exit data for node attributes.

    Returns:
        NetworkX DiGraph with all road and node attributes.
    """
    graph = nx.DiGraph()

    # Add zone nodes
    if zones:
        for zone_id, zone_data in zones.items():
            graph.add_node(
                zone_id,
                type="zone",
                name=zone_data.get("name", zone_id),
                lat=zone_data.get("center_lat", zone_data.get("center", {}).get("lat", 0)),
                lon=zone_data.get("center_lon", zone_data.get("center", {}).get("lon", 0)),
                crowd_count=zone_data.get("crowd_count", zone_data.get("initial_crowd", 0)),
            )

    # Add exit nodes
    if exits:
        for exit_id, exit_data in exits.items():
            graph.add_node(
                exit_id,
                type="exit",
                name=exit_data.get("name", exit_id),
                lat=exit_data.get("lat", exit_data.get("location", {}).get("lat", 0)),
                lon=exit_data.get("lon", exit_data.get("location", {}).get("lon", 0)),
                capacity=exit_data.get("capacity", 0),
                flow_rate=exit_data.get("flow_rate", 0),
            )

    # Add edges
    for road_id, road in roads.items():
        from_node = road.get("from_node", "")
        to_node = road.get("to_node", "")
        if not from_node or not to_node:
            continue

        attrs = {
            "road_id": road_id,
            "name": road.get("name", road_id),
            "length": road.get("length", 100.0),
            "travel_time": road.get("travel_time", 5.0),
            "capacity": road.get("capacity", 500),
            "congestion": road.get("congestion", road.get("initial_congestion", 0.0)),
            "risk": road.get("risk", 0.0),
            "blocked": road.get("blocked", False),
        }

        graph.add_edge(from_node, to_node, **attrs)
        graph.add_edge(to_node, from_node, **attrs)

    logger.info(
        "Built graph: %d nodes, %d edges",
        graph.number_of_nodes(), graph.number_of_edges(),
    )
    return graph
