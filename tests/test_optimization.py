"""Tests for optimization."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from agents.tools import (
    build_road_graph, find_all_zone_exit_routes,
    optimize_evacuation_assignment, calculate_zone_risk_score,
)
from optimization.constraints import check_exit_capacity


def test_find_all_routes(demo_roads, demo_zones, demo_exits):
    graph = build_road_graph(demo_roads)
    routes = find_all_zone_exit_routes(graph, demo_zones, demo_exits)
    assert len(routes) == len(demo_zones)
    for zone_id, zone_routes in routes.items():
        assert len(zone_routes) == len(demo_exits)


def test_optimize_assignment(demo_roads, demo_zones, demo_exits):
    graph = build_road_graph(demo_roads)
    routes = find_all_zone_exit_routes(graph, demo_zones, demo_exits)
    assignments = optimize_evacuation_assignment(demo_zones, demo_exits, routes)
    assert len(assignments) == len(demo_zones)
    total = sum(a["people"] for assigns in assignments.values() for a in assigns)
    assert total > 0


def test_risk_score():
    score, level = calculate_zone_risk_score(
        zone={}, crowd_density=0.8,
        nearby_road_congestion=0.5, blocked_exit_ratio=0.0,
        emergency_proximity=0.7, structural_risk=0.1,
    )
    assert 0 <= score <= 1
    assert level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_exit_capacity_check(demo_exits):
    assignments = {
        "zone_a": [{"exit_id": "exit_north", "people": 2000}],
    }
    violations = check_exit_capacity(demo_exits, assignments)
    assert len(violations) > 0
    assert violations[0]["exit_id"] == "exit_north"
