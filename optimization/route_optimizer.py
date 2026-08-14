"""
Route Optimizer — Dijkstra with custom cost function.

Wraps NetworkX shortest path with the multi-criteria cost function.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from optimization.cost_function import compute_cost

logger = logging.getLogger(__name__)


def find_optimal_route(
    graph: nx.DiGraph,
    source: str,
    target: str,
    cost_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Find optimal route using Dijkstra with custom cost.

    Args:
        graph: Road network graph.
        source: Source node ID.
        target: Target node ID.
        cost_weights: Cost function weights.

    Returns:
        Route dict with path, cost, travel_time, distance, feasible.
    """
    if source not in graph or target not in graph:
        return {"path": [], "cost": float("inf"), "feasible": False,
                "reason": f"Missing node: {source} or {target}"}

    def weight_fn(u: str, v: str, data: dict) -> float:
        return compute_cost(data, cost_weights)

    try:
        path = nx.dijkstra_path(graph, source, target, weight=weight_fn)
        cost = nx.dijkstra_path_length(graph, source, target, weight=weight_fn)

        total_time = sum(
            graph[path[i]][path[i + 1]].get("travel_time", 0.0)
            for i in range(len(path) - 1)
        )
        total_dist = sum(
            graph[path[i]][path[i + 1]].get("length", 0.0)
            for i in range(len(path) - 1)
        )

        feasible = cost < 999_999.0
        return {
            "path": path,
            "cost": round(cost, 4),
            "travel_time": round(total_time, 2),
            "distance": round(total_dist, 2),
            "feasible": feasible,
            "reason": "" if feasible else "Route through blocked road",
        }
    except nx.NetworkXNoPath:
        return {"path": [], "cost": float("inf"), "feasible": False,
                "reason": f"No path from {source} to {target}"}


def find_k_shortest(
    graph: nx.DiGraph,
    source: str,
    target: str,
    k: int = 3,
    cost_weights: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Find k-shortest simple paths.

    Args:
        graph: Road network graph.
        source: Source node.
        target: Target node.
        k: Number of paths.
        cost_weights: Cost weights.

    Returns:
        List of route dicts sorted by cost.
    """
    if source not in graph or target not in graph:
        return []

    def weight_fn(u: str, v: str, data: dict) -> float:
        return compute_cost(data, cost_weights)

    try:
        paths = list(nx.shortest_simple_paths(graph, source, target, weight=weight_fn))
        routes = []
        for path in paths[:k]:
            cost = sum(weight_fn(path[i], path[i + 1], graph[path[i]][path[i + 1]])
                       for i in range(len(path) - 1))
            total_time = sum(graph[path[i]][path[i + 1]].get("travel_time", 0.0)
                             for i in range(len(path) - 1))
            total_dist = sum(graph[path[i]][path[i + 1]].get("length", 0.0)
                             for i in range(len(path) - 1))
            routes.append({
                "path": path, "cost": round(cost, 4),
                "travel_time": round(total_time, 2),
                "distance": round(total_dist, 2),
                "feasible": cost < 999_999.0,
            })
        return routes
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []
