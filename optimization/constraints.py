"""
Constraints — Exit and road capacity validation.
"""

from __future__ import annotations

from typing import Any


def check_exit_capacity(
    exits: dict[str, dict[str, Any]],
    assignments: dict[str, list[dict[str, Any]]],
    safety_factor: float = 0.85,
) -> list[dict[str, Any]]:
    """Check if exit capacity constraints are satisfied.

    Args:
        exits: Exit data.
        assignments: Zone-to-exit assignments.
        safety_factor: Fraction of capacity to use.

    Returns:
        List of violation dicts for overloaded exits.
    """
    exit_loads: dict[str, int] = {eid: 0 for eid in exits}
    for zone_assigns in assignments.values():
        for a in zone_assigns:
            eid = a.get("exit_id", "")
            if eid in exit_loads:
                exit_loads[eid] += a.get("people", 0)

    violations = []
    for eid, load in exit_loads.items():
        cap = int(exits.get(eid, {}).get("capacity", 0) * safety_factor)
        if load > cap:
            violations.append({
                "exit_id": eid,
                "load": load,
                "capacity": cap,
                "overflow": load - cap,
            })
    return violations


def check_road_capacity(
    roads: dict[str, dict[str, Any]],
    assignments: dict[str, list[dict[str, Any]]],
    safety_factor: float = 0.80,
) -> list[dict[str, Any]]:
    """Check if road capacity constraints are satisfied.

    Args:
        roads: Road data.
        assignments: Assignments with route paths.
        safety_factor: Fraction of capacity to use.

    Returns:
        List of violation dicts for overloaded roads.
    """
    road_loads: dict[str, int] = {rid: 0 for rid in roads}

    for zone_assigns in assignments.values():
        for a in zone_assigns:
            people = a.get("people", 0)
            route = a.get("route", [])
            # Each edge in route carries these people
            for i in range(len(route) - 1):
                for rid, rdata in roads.items():
                    fn = rdata.get("from_node", "")
                    tn = rdata.get("to_node", "")
                    if ((fn == route[i] and tn == route[i + 1]) or
                            (tn == route[i] and fn == route[i + 1])):
                        road_loads[rid] = road_loads.get(rid, 0) + people

    violations = []
    for rid, load in road_loads.items():
        cap = int(roads.get(rid, {}).get("capacity", 0) * safety_factor)
        if cap > 0 and load > cap:
            violations.append({
                "road_id": rid,
                "load": load,
                "capacity": cap,
                "overflow": load - cap,
            })
    return violations
