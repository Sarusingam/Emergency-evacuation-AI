"""
Agent Tools — Deterministic Computation Functions.

This module provides the core computational tools that agents use
for route calculation, risk scoring, and evacuation optimization.

IMPORTANT DESIGN DECISION:
All numerical/routing calculations are done by these deterministic
functions, NOT by an LLM. The LLM (in the coordinator) only reasons
about strategy and decisions — it never invents route numbers.

Tools are available both as:
1. Regular Python functions (called directly by agents).
2. LangChain @tool wrappers (available to the coordinator LLM).

Dependencies: networkx (graphs), scipy (LP optimization).

Input: Road/zone/exit data as Python dicts.
Output: Computed routes, risk scores, and evacuation assignments.
"""

from __future__ import annotations

import json
import logging
import math
from typing import Any

import networkx as nx
import numpy as np
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ── Module-level context for LangChain tools ────────────────────
# The coordinator sets this before calling LLM with tools so that
# @tool functions can access current state without explicit args.
_current_state: dict[str, Any] = {}


def set_tool_context(state: dict[str, Any]) -> None:
    """Set the current state context for LangChain tool functions.

    Call this before invoking the LLM with tools so that tool
    functions can read the current evacuation state.

    Args:
        state: The current EvacuationState dict.
    """
    global _current_state
    _current_state = state


# ================================================================
# CORE COMPUTATION FUNCTIONS (called directly by agents)
# ================================================================


def build_road_graph(roads: dict[str, dict[str, Any]]) -> nx.DiGraph:
    """Build a NetworkX directed graph from road data.

    Each road becomes two directed edges (bidirectional travel).
    Edge attributes include length, travel_time, capacity,
    congestion, risk, and blocked status.

    Args:
        roads: Dict of road_id -> road data dict.

    Returns:
        NetworkX DiGraph with road attributes on edges.
    """
    graph = nx.DiGraph()

    for road_id, road in roads.items():
        from_node = road.get("from_node", "")
        to_node = road.get("to_node", "")

        if not from_node or not to_node:
            logger.warning("Road %s missing from/to nodes, skipping", road_id)
            continue

        attrs = {
            "road_id": road_id,
            "name": road.get("name", road_id),
            "length": road.get("length", 100.0),
            "travel_time": road.get("travel_time", 5.0),
            "capacity": road.get("capacity", 500),
            "congestion": road.get("congestion", 0.0),
            "risk": road.get("risk", 0.0),
            "blocked": road.get("blocked", False),
        }

        # Add edges in both directions (bidirectional roads)
        graph.add_edge(from_node, to_node, **attrs)
        graph.add_edge(to_node, from_node, **attrs)

    logger.debug(
        "Built road graph: %d nodes, %d edges",
        graph.number_of_nodes(),
        graph.number_of_edges(),
    )
    return graph


def compute_edge_cost(
    edge_data: dict[str, Any],
    cost_weights: dict[str, float] | None = None,
    blocked_cost: float = 999_999.0,
) -> float:
    """Compute the weighted cost of traversing a road edge.

    Cost formula:
        cost = w_dist * normalized_distance
             + w_time * normalized_time
             + w_cong * congestion
             + w_risk * risk

    Blocked roads receive an effectively infinite cost.

    Args:
        edge_data: Edge attributes from the NetworkX graph.
        cost_weights: Dict with keys 'distance', 'travel_time',
                      'congestion', 'risk'. Defaults provided.
        blocked_cost: Cost assigned to blocked roads.

    Returns:
        Computed cost as a float.
    """
    if edge_data.get("blocked", False):
        return blocked_cost

    weights = cost_weights or {
        "distance": 0.25,
        "travel_time": 0.30,
        "congestion": 0.25,
        "risk": 0.20,
    }

    # Normalize distance and time to 0-1 range
    # Using typical urban values as reference
    norm_distance = min(edge_data.get("length", 100.0) / 1000.0, 1.0)
    norm_time = min(edge_data.get("travel_time", 5.0) / 15.0, 1.0)
    congestion = edge_data.get("congestion", 0.0)
    risk = edge_data.get("risk", 0.0)

    cost = (
        weights.get("distance", 0.25) * norm_distance
        + weights.get("travel_time", 0.30) * norm_time
        + weights.get("congestion", 0.25) * congestion
        + weights.get("risk", 0.20) * risk
    )

    return max(cost, 0.001)  # Ensure positive cost


def find_shortest_path(
    graph: nx.DiGraph,
    source: str,
    target: str,
    cost_weights: dict[str, float] | None = None,
    blocked_cost: float = 999_999.0,
) -> dict[str, Any]:
    """Find the shortest path between two nodes using custom cost.

    Uses Dijkstra's algorithm with the weighted cost function.

    Args:
        graph: NetworkX DiGraph with road attributes.
        source: Source node ID (zone or exit).
        target: Target node ID (zone or exit).
        cost_weights: Cost function weights.
        blocked_cost: Cost for blocked roads.

    Returns:
        Dict with 'path' (list of node IDs), 'cost' (total cost),
        'travel_time' (total minutes), 'distance' (total meters),
        and 'feasible' (bool). Returns feasible=False if no path.
    """
    if source not in graph or target not in graph:
        return {
            "path": [],
            "cost": float("inf"),
            "travel_time": 0.0,
            "distance": 0.0,
            "feasible": False,
            "reason": f"Node not in graph: {source} or {target}",
        }

    # Custom weight function for Dijkstra
    def weight_fn(u: str, v: str, data: dict) -> float:
        return compute_edge_cost(data, cost_weights, blocked_cost)

    try:
        path = nx.dijkstra_path(graph, source, target, weight=weight_fn)
        cost = nx.dijkstra_path_length(graph, source, target, weight=weight_fn)

        # Sum travel time and distance along path
        total_time = 0.0
        total_distance = 0.0
        for i in range(len(path) - 1):
            edge_data = graph[path[i]][path[i + 1]]
            total_time += edge_data.get("travel_time", 0.0)
            total_distance += edge_data.get("length", 0.0)

        # Check if path uses blocked roads (cost would be huge)
        feasible = cost < blocked_cost

        return {
            "path": path,
            "cost": round(cost, 4),
            "travel_time": round(total_time, 2),
            "distance": round(total_distance, 2),
            "feasible": feasible,
            "reason": "" if feasible else "Path goes through blocked road",
        }

    except nx.NetworkXNoPath:
        return {
            "path": [],
            "cost": float("inf"),
            "travel_time": 0.0,
            "distance": 0.0,
            "feasible": False,
            "reason": f"No path from {source} to {target}",
        }


def find_all_zone_exit_routes(
    graph: nx.DiGraph,
    zones: dict[str, dict],
    exits: dict[str, dict],
    cost_weights: dict[str, float] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Find shortest routes from every zone to every exit.

    Args:
        graph: NetworkX DiGraph.
        zones: Zone data dict.
        exits: Exit data dict.
        cost_weights: Cost function weights.

    Returns:
        Dict of zone_id -> list of route dicts (one per exit),
        sorted by cost (cheapest first).
    """
    all_routes: dict[str, list[dict[str, Any]]] = {}

    for zone_id in zones:
        zone_routes: list[dict[str, Any]] = []
        for exit_id in exits:
            route = find_shortest_path(
                graph, zone_id, exit_id, cost_weights
            )
            route["zone_id"] = zone_id
            route["exit_id"] = exit_id
            zone_routes.append(route)

        # Sort by cost (feasible routes first, then by cost)
        zone_routes.sort(key=lambda r: (not r["feasible"], r["cost"]))
        all_routes[zone_id] = zone_routes

    return all_routes


def optimize_evacuation_assignment(
    zones: dict[str, dict],
    exits: dict[str, dict],
    routes: dict[str, list[dict]],
    exit_safety_factor: float = 0.85,
) -> dict[str, list[dict[str, Any]]]:
    """Optimize the assignment of people from zones to exits.

    Uses scipy linear programming to minimize total evacuation cost
    while respecting exit capacity constraints.

    Decision variables: x[z][e] = number of people from zone z to exit e.
    Objective: minimize sum(x[z][e] * route_cost[z][e]).
    Constraints:
        - sum_e(x[z][e]) = zone_crowd[z]  (all people evacuated)
        - sum_z(x[z][e]) <= exit_capacity[e]  (exit not overloaded)
        - x[z][e] >= 0
        - x[z][e] = 0 if route is infeasible

    Falls back to greedy assignment if scipy is unavailable or LP fails.

    Args:
        zones: Zone data with crowd_count.
        exits: Exit data with capacity.
        routes: Routes from find_all_zone_exit_routes().
        exit_safety_factor: Fraction of exit capacity to use.

    Returns:
        Dict of zone_id -> list of {exit_id, people, route, cost}.
    """
    zone_ids = sorted(zones.keys())
    exit_ids = sorted(exits.keys())
    n_zones = len(zone_ids)
    n_exits = len(exit_ids)

    if n_zones == 0 or n_exits == 0:
        return {}

    # Build cost matrix and feasibility matrix
    cost_matrix = np.full((n_zones, n_exits), 999_999.0)
    feasible_matrix = np.zeros((n_zones, n_exits), dtype=bool)

    for i, zone_id in enumerate(zone_ids):
        zone_routes = routes.get(zone_id, [])
        for route in zone_routes:
            exit_id = route.get("exit_id", "")
            if exit_id in exit_ids:
                j = exit_ids.index(exit_id)
                if route.get("feasible", False):
                    cost_matrix[i, j] = route["cost"]
                    feasible_matrix[i, j] = True

    # Get crowd counts and exit capacities
    crowd_counts = [
        zones[z_id].get("crowd_count", 0) for z_id in zone_ids
    ]
    exit_capacities = [
        int(exits[e_id].get("capacity", 0) * exit_safety_factor)
        for e_id in exit_ids
    ]

    total_people = sum(crowd_counts)
    total_capacity = sum(exit_capacities)

    if total_people == 0:
        return {z_id: [] for z_id in zone_ids}

    # Try scipy LP first
    try:
        from scipy.optimize import linprog

        # Decision variables: x[i*n_exits + j] = people from zone i to exit j
        n_vars = n_zones * n_exits

        # Bounds: 0 <= x[i,j], infeasible routes forced to 0
        bounds = []
        for i in range(n_zones):
            for j in range(n_exits):
                if feasible_matrix[i, j]:
                    bounds.append((0.0, float(crowd_counts[i])))
                else:
                    bounds.append((0.0, 0.0))

        if total_capacity < total_people:
            logger.warning(
                "Total exit capacity (%d) < total people (%d). "
                "Not everyone can be evacuated.",
                total_capacity, total_people,
            )
            # MAXIMIZE people evacuated (negate objective = -1 per person + tiny cost tiebreaker)
            # This ensures the LP assigns as many people as possible.
            c = np.array([
                -1.0 + cost_matrix[i, j] * 1e-6
                for i in range(n_zones)
                for j in range(n_exits)
            ])

            # Upper bound constraints: exit capacity
            A_ub = np.zeros((n_exits, n_vars))
            b_ub = np.array(exit_capacities, dtype=float)
            for j in range(n_exits):
                for i in range(n_zones):
                    A_ub[j, i * n_exits + j] = 1.0

            # Upper bound constraints: zone people (can't evacuate more than exist)
            A_zone_ub = np.zeros((n_zones, n_vars))
            b_zone_ub = np.array(crowd_counts, dtype=float)
            for i in range(n_zones):
                for j in range(n_exits):
                    A_zone_ub[i, i * n_exits + j] = 1.0

            A_ub_full = np.vstack([A_ub, A_zone_ub])
            b_ub_full = np.concatenate([b_ub, b_zone_ub])

            result = linprog(
                c, A_ub=A_ub_full, b_ub=b_ub_full,
                bounds=bounds, method="highs",
            )
        else:
            c = cost_matrix.flatten()  # Objective: minimize cost
            # Equality constraints: all people from each zone must be assigned
            A_eq = np.zeros((n_zones, n_vars))
            b_eq = np.array(crowd_counts, dtype=float)
            for i in range(n_zones):
                for j in range(n_exits):
                    A_eq[i, i * n_exits + j] = 1.0

            # Inequality constraints: exit capacity
            A_ub = np.zeros((n_exits, n_vars))
            b_ub = np.array(exit_capacities, dtype=float)
            for j in range(n_exits):
                for i in range(n_zones):
                    A_ub[j, i * n_exits + j] = 1.0

            result = linprog(
                c, A_ub=A_ub, b_ub=b_ub,
                A_eq=A_eq, b_eq=b_eq,
                bounds=bounds, method="highs",
            )

        if result.success:
            assignment = _parse_lp_result(
                result.x, zone_ids, exit_ids, routes, n_exits
            )
            total_assigned = sum(
                a["people"] for assigns in assignment.values() for a in assigns
            )
            logger.info("LP optimization succeeded: %d people assigned", total_assigned)
            return assignment
        else:
            logger.warning(
                "LP optimization failed: %s. Falling back to greedy.",
                result.message,
            )

    except ImportError:
        logger.warning("scipy not available, using greedy assignment")
    except Exception as exc:
        logger.warning("LP optimization error: %s. Using greedy.", exc)

    # Fallback: greedy assignment
    return _greedy_assignment(
        zone_ids, exit_ids, zones, exits, routes,
        exit_capacities, cost_matrix, feasible_matrix,
    )


def _parse_lp_result(
    x: np.ndarray,
    zone_ids: list[str],
    exit_ids: list[str],
    routes: dict[str, list[dict]],
    n_exits: int,
) -> dict[str, list[dict[str, Any]]]:
    """Parse LP result into assignment dict.

    Args:
        x: Solution vector from linprog.
        zone_ids: Ordered list of zone IDs.
        exit_ids: Ordered list of exit IDs.
        routes: Route data from find_all_zone_exit_routes.
        n_exits: Number of exits.

    Returns:
        Assignment dict: zone_id -> list of {exit_id, people, route, cost}.
    """
    assignment: dict[str, list[dict[str, Any]]] = {}

    for i, zone_id in enumerate(zone_ids):
        zone_assignments: list[dict[str, Any]] = []
        zone_routes = routes.get(zone_id, [])

        for j, exit_id in enumerate(exit_ids):
            people = int(round(x[i * n_exits + j]))
            if people > 0:
                # Find matching route
                route_data = next(
                    (r for r in zone_routes if r.get("exit_id") == exit_id),
                    {},
                )
                zone_assignments.append({
                    "exit_id": exit_id,
                    "people": people,
                    "route": route_data.get("path", []),
                    "cost": route_data.get("cost", 0.0),
                    "travel_time": route_data.get("travel_time", 0.0),
                })

        assignment[zone_id] = zone_assignments

    return assignment


def _greedy_assignment(
    zone_ids: list[str],
    exit_ids: list[str],
    zones: dict[str, dict],
    exits: dict[str, dict],
    routes: dict[str, list[dict]],
    exit_capacities: list[int],
    cost_matrix: np.ndarray,
    feasible_matrix: np.ndarray,
) -> dict[str, list[dict[str, Any]]]:
    """Greedy fallback for evacuation assignment.

    Assigns people from each zone to the cheapest available exit
    until exit capacity is reached.

    Args:
        zone_ids: Zone IDs.
        exit_ids: Exit IDs.
        zones: Zone data.
        exits: Exit data.
        routes: Route data.
        exit_capacities: Safe capacity per exit.
        cost_matrix: Cost matrix [zones x exits].
        feasible_matrix: Feasibility matrix [zones x exits].

    Returns:
        Assignment dict.
    """
    remaining_capacity = list(exit_capacities)
    assignment: dict[str, list[dict[str, Any]]] = {}

    for i, zone_id in enumerate(zone_ids):
        remaining_people = zones[zone_id].get("crowd_count", 0)
        zone_assignments: list[dict[str, Any]] = []
        zone_routes = routes.get(zone_id, [])

        # Sort exits by cost for this zone
        exit_order = sorted(
            range(len(exit_ids)),
            key=lambda j: cost_matrix[i, j] if feasible_matrix[i, j] else float("inf"),
        )

        for j in exit_order:
            if remaining_people <= 0:
                break
            if not feasible_matrix[i, j]:
                continue
            if remaining_capacity[j] <= 0:
                continue

            assign_count = min(remaining_people, remaining_capacity[j])
            remaining_capacity[j] -= assign_count
            remaining_people -= assign_count

            exit_id = exit_ids[j]
            route_data = next(
                (r for r in zone_routes if r.get("exit_id") == exit_id),
                {},
            )
            zone_assignments.append({
                "exit_id": exit_id,
                "people": assign_count,
                "route": route_data.get("path", []),
                "cost": route_data.get("cost", 0.0),
                "travel_time": route_data.get("travel_time", 0.0),
            })

        assignment[zone_id] = zone_assignments

    return assignment


def calculate_zone_risk_score(
    zone: dict[str, Any],
    crowd_density: float,
    nearby_road_congestion: float,
    blocked_exit_ratio: float,
    emergency_proximity: float = 0.5,
    structural_risk: float = 0.1,
    weights: dict[str, float] | None = None,
) -> tuple[float, str]:
    """Calculate a zone's risk score and level.

    Args:
        zone: Zone data dict.
        crowd_density: Normalized crowd density (0-1 scale).
        nearby_road_congestion: Average congestion of nearby roads (0-1).
        blocked_exit_ratio: Fraction of exits that are blocked (0-1).
        emergency_proximity: How close the zone is to the emergency (0-1).
        structural_risk: Structural risk of the zone (0-1).
        weights: Risk factor weights.

    Returns:
        Tuple of (risk_score: float 0-1, risk_level: str).
    """
    w = weights or {
        "crowd_density": 0.30,
        "emergency_proximity": 0.25,
        "road_congestion": 0.20,
        "blocked_exits": 0.15,
        "structural_risk": 0.10,
    }

    score = (
        w.get("crowd_density", 0.3) * min(crowd_density, 1.0)
        + w.get("emergency_proximity", 0.25) * min(emergency_proximity, 1.0)
        + w.get("road_congestion", 0.2) * min(nearby_road_congestion, 1.0)
        + w.get("blocked_exits", 0.15) * min(blocked_exit_ratio, 1.0)
        + w.get("structural_risk", 0.1) * min(structural_risk, 1.0)
    )

    score = round(min(max(score, 0.0), 1.0), 4)

    # Classify into risk level
    if score >= 0.75:
        level = "CRITICAL"
    elif score >= 0.50:
        level = "HIGH"
    elif score >= 0.25:
        level = "MEDIUM"
    else:
        level = "LOW"

    return score, level


# ================================================================
# LANGCHAIN TOOL WRAPPERS (for coordinator LLM)
# ================================================================
# These tools access _current_state set by set_tool_context().
# The coordinator sets context before invoking the LLM.
# ================================================================


@tool
def check_zone_status(zone_id: str) -> str:
    """Check the current crowd count, density, and risk for a zone.

    Args:
        zone_id: The zone identifier (e.g., 'zone_a').

    Returns:
        JSON string with zone status details.
    """
    zones = _current_state.get("zones", {})
    crowd = _current_state.get("crowd_analysis", {}).get("zones", {})
    risk = _current_state.get("risk_assessment", {}).get("zones", {})

    zone_info = zones.get(zone_id, {})
    crowd_info = crowd.get(zone_id, {})
    risk_info = risk.get(zone_id, {})

    if not zone_info:
        return json.dumps({"error": f"Zone {zone_id} not found"})

    result = {
        "zone_id": zone_id,
        "name": zone_info.get("name", zone_id),
        "crowd_count": crowd_info.get("count", zone_info.get("crowd_count", 0)),
        "density": crowd_info.get("density", 0),
        "density_level": crowd_info.get("density_level", "unknown"),
        "risk_level": risk_info.get("risk_level", "unknown"),
        "risk_score": risk_info.get("risk_score", 0),
    }
    return json.dumps(result, indent=2)


@tool
def check_road_conditions(road_id: str) -> str:
    """Check the current status of a specific road.

    Args:
        road_id: The road identifier (e.g., 'road_r1').

    Returns:
        JSON string with road conditions.
    """
    roads = _current_state.get("roads", {})
    traffic = _current_state.get("traffic_status", {}).get("roads", {})

    road_info = roads.get(road_id, {})
    traffic_info = traffic.get(road_id, {})

    if not road_info:
        return json.dumps({"error": f"Road {road_id} not found"})

    result = {
        "road_id": road_id,
        "name": road_info.get("name", road_id),
        "blocked": road_info.get("blocked", False),
        "congestion": traffic_info.get("congestion", road_info.get("congestion", 0)),
        "capacity": road_info.get("capacity", 0),
        "available_capacity": traffic_info.get("available_capacity", road_info.get("capacity", 0)),
    }
    return json.dumps(result, indent=2)


@tool
def get_evacuation_progress() -> str:
    """Get a summary of current evacuation progress.

    Returns:
        JSON string with evacuation statistics.
    """
    plan = _current_state.get("evacuation_plan", {})
    zones = _current_state.get("zones", {})

    total_people = sum(
        z.get("crowd_count", 0) for z in zones.values()
    )
    assigned = 0
    assignments = plan.get("assignments", {})
    for zone_assigns in assignments.values():
        for a in zone_assigns:
            assigned += a.get("people", 0)

    result = {
        "total_people": total_people,
        "people_assigned_routes": assigned,
        "estimated_time": plan.get("estimated_total_time", 0),
        "plan_status": plan.get("status", "not_generated"),
        "replan_count": _current_state.get("replan_count", 0),
    }
    return json.dumps(result, indent=2)


@tool
def request_replan(reason: str) -> str:
    """Request that evacuation routes be recalculated.

    Use this when conditions have changed significantly.

    Args:
        reason: Explanation of why replanning is needed.

    Returns:
        Confirmation message.
    """
    # This tool is advisory — the coordinator reads the result
    # and sets the needs_replan flag in state.
    return json.dumps({
        "action": "replan_requested",
        "reason": reason,
        "status": "The coordinator will trigger replanning.",
    })


# List of all LangChain tools for the coordinator LLM
COORDINATOR_TOOLS = [
    check_zone_status,
    check_road_conditions,
    get_evacuation_progress,
    request_replan,
]
