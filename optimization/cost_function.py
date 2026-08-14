"""
Cost Function — Weighted multi-criteria route cost.

Computes: cost = w₁·dist + w₂·time + w₃·congestion + w₄·risk
Blocked roads → infinite cost.
"""

from __future__ import annotations

from typing import Any

DEFAULT_WEIGHTS = {
    "distance": 0.25,
    "travel_time": 0.30,
    "congestion": 0.25,
    "risk": 0.20,
}

BLOCKED_COST = 999_999.0


def compute_cost(
    edge: dict[str, Any],
    weights: dict[str, float] | None = None,
    blocked_cost: float = BLOCKED_COST,
) -> float:
    """Compute weighted traversal cost for a road edge.

    Args:
        edge: Edge attributes dict.
        weights: Cost weights (distance, travel_time, congestion, risk).
        blocked_cost: Cost for blocked roads.

    Returns:
        Computed cost (positive float).
    """
    if edge.get("blocked", False):
        return blocked_cost

    w = weights or DEFAULT_WEIGHTS
    norm_dist = min(edge.get("length", 100.0) / 1000.0, 1.0)
    norm_time = min(edge.get("travel_time", 5.0) / 15.0, 1.0)
    congestion = min(edge.get("congestion", 0.0), 1.0)
    risk = min(edge.get("risk", 0.0), 1.0)

    cost = (
        w.get("distance", 0.25) * norm_dist
        + w.get("travel_time", 0.30) * norm_time
        + w.get("congestion", 0.25) * congestion
        + w.get("risk", 0.20) * risk
    )
    return max(cost, 0.001)
