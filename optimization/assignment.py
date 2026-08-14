"""
Assignment Solver — Zone-to-exit assignment.

High-level interface that combines route finding and LP optimization.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import networkx as nx

from optimization.cost_function import compute_cost
from optimization.evacuation_optimizer import optimize_assignment

logger = logging.getLogger(__name__)


def solve_evacuation_assignment(
    graph: nx.DiGraph,
    zones: dict[str, dict[str, Any]],
    exits: dict[str, dict[str, Any]],
    cost_weights: dict[str, float] | None = None,
    exit_safety_factor: float = 0.85,
) -> dict[str, Any]:
    """Solve the full evacuation assignment problem.

    Args:
        graph: Road network graph.
        zones: Zone data with crowd_count.
        exits: Exit data with capacity.
        cost_weights: Cost function weights.
        exit_safety_factor: Exit capacity safety factor.

    Returns:
        Dict with 'assignments', 'total_people', 'total_assigned',
        'unassigned', 'estimated_time'.
    """
    zone_ids = sorted(zones.keys())
    exit_ids = sorted(exits.keys())
    n_z, n_e = len(zone_ids), len(exit_ids)

    if n_z == 0 or n_e == 0:
        return {"assignments": {}, "total_people": 0, "total_assigned": 0}

    # Build cost and feasibility matrices
    cost_matrix = np.full((n_z, n_e), 999_999.0)
    feasible = np.zeros((n_z, n_e), dtype=bool)
    route_paths: dict[tuple[int, int], list[str]] = {}

    for i, zid in enumerate(zone_ids):
        for j, eid in enumerate(exit_ids):
            if zid not in graph or eid not in graph:
                continue
            try:
                def wf(u, v, d):
                    return compute_cost(d, cost_weights)
                path = nx.dijkstra_path(graph, zid, eid, weight=wf)
                cost = nx.dijkstra_path_length(graph, zid, eid, weight=wf)
                if cost < 999_999.0:
                    cost_matrix[i, j] = cost
                    feasible[i, j] = True
                    route_paths[(i, j)] = path
            except nx.NetworkXNoPath:
                pass

    crowd_counts = [zones[z].get("crowd_count", 0) for z in zone_ids]
    exit_caps = [int(exits[e].get("capacity", 0) * exit_safety_factor) for e in exit_ids]

    assignments = optimize_assignment(
        zone_ids, exit_ids, crowd_counts, exit_caps, cost_matrix, feasible
    )

    # Enrich with route paths
    for i, zid in enumerate(zone_ids):
        for a in assignments.get(zid, []):
            j = exit_ids.index(a["exit_id"])
            a["route"] = route_paths.get((i, j), [])

    total = sum(crowd_counts)
    assigned = sum(a["people"] for assigns in assignments.values() for a in assigns)

    return {
        "assignments": assignments,
        "total_people": total,
        "total_assigned": assigned,
        "unassigned": total - assigned,
    }
