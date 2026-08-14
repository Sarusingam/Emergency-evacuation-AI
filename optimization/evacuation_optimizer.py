"""
Evacuation Optimizer — Multi-zone people-to-exit assignment via LP.

Uses scipy.optimize.linprog to distribute people optimally across
exits while respecting capacity constraints.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def optimize_assignment(
    zone_ids: list[str],
    exit_ids: list[str],
    crowd_counts: list[int],
    exit_capacities: list[int],
    cost_matrix: np.ndarray,
    feasible_matrix: np.ndarray,
) -> dict[str, list[dict[str, Any]]]:
    """Optimize zone-to-exit people assignment.

    Args:
        zone_ids: Ordered zone IDs.
        exit_ids: Ordered exit IDs.
        crowd_counts: People per zone.
        exit_capacities: Max people per exit.
        cost_matrix: Cost[zone][exit] array.
        feasible_matrix: Boolean feasibility[zone][exit].

    Returns:
        Dict zone_id -> list of {exit_id, people, cost}.
    """
    n_z, n_e = len(zone_ids), len(exit_ids)
    if n_z == 0 or n_e == 0:
        return {}

    try:
        from scipy.optimize import linprog

        n_vars = n_z * n_e
        c = cost_matrix.flatten()

        # Equality: all people from each zone assigned
        A_eq = np.zeros((n_z, n_vars))
        b_eq = np.array(crowd_counts, dtype=float)
        for i in range(n_z):
            for j in range(n_e):
                A_eq[i, i * n_e + j] = 1.0

        # Inequality: exit capacity
        A_ub = np.zeros((n_e, n_vars))
        b_ub = np.array(exit_capacities, dtype=float)
        for j in range(n_e):
            for i in range(n_z):
                A_ub[j, i * n_e + j] = 1.0

        bounds = []
        for i in range(n_z):
            for j in range(n_e):
                ub = float(crowd_counts[i]) if feasible_matrix[i, j] else 0.0
                bounds.append((0.0, ub))

        total_cap = sum(exit_capacities)
        total_ppl = sum(crowd_counts)

        if total_cap < total_ppl:
            result = linprog(c, A_ub=np.vstack([A_ub, A_eq]),
                             b_ub=np.concatenate([b_ub, b_eq]),
                             bounds=bounds, method="highs")
        else:
            result = linprog(c, A_ub=A_ub, b_ub=b_ub,
                             A_eq=A_eq, b_eq=b_eq,
                             bounds=bounds, method="highs")

        if result.success:
            return _parse_result(result.x, zone_ids, exit_ids, n_e, cost_matrix)

        logger.warning("LP failed: %s, using greedy", result.message)
    except ImportError:
        logger.warning("scipy unavailable, using greedy")
    except Exception as e:
        logger.warning("LP error: %s, using greedy", e)

    return _greedy_assign(zone_ids, exit_ids, crowd_counts, exit_capacities,
                          cost_matrix, feasible_matrix)


def _parse_result(x, zone_ids, exit_ids, n_e, cost_matrix):
    assignment = {}
    for i, zid in enumerate(zone_ids):
        assigns = []
        for j, eid in enumerate(exit_ids):
            people = int(round(x[i * n_e + j]))
            if people > 0:
                assigns.append({"exit_id": eid, "people": people,
                                "cost": round(float(cost_matrix[i, j]), 4)})
        assignment[zid] = assigns
    return assignment


def _greedy_assign(zone_ids, exit_ids, crowd_counts, exit_capacities,
                   cost_matrix, feasible_matrix):
    remaining_cap = list(exit_capacities)
    assignment = {}
    for i, zid in enumerate(zone_ids):
        remaining = crowd_counts[i]
        assigns = []
        order = sorted(range(len(exit_ids)),
                       key=lambda j: cost_matrix[i, j] if feasible_matrix[i, j] else float("inf"))
        for j in order:
            if remaining <= 0 or not feasible_matrix[i, j] or remaining_cap[j] <= 0:
                continue
            n = min(remaining, remaining_cap[j])
            remaining_cap[j] -= n
            remaining -= n
            assigns.append({"exit_id": exit_ids[j], "people": n,
                            "cost": round(float(cost_matrix[i, j]), 4)})
        assignment[zid] = assigns
    return assignment
