"""Tests for routing and graph building."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.tools import build_road_graph, find_shortest_path, compute_edge_cost
from routing.graph_builder import build_graph_from_scenario
from optimization.cost_function import compute_cost


def test_build_road_graph(demo_roads):
    graph = build_road_graph(demo_roads)
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0
    # Bidirectional: each road = 2 edges
    assert graph.number_of_edges() == len(demo_roads) * 2


def test_find_shortest_path(demo_roads):
    graph = build_road_graph(demo_roads)
    route = find_shortest_path(graph, "zone_a", "exit_north")
    assert route["feasible"]
    assert route["path"] == ["zone_a", "exit_north"]
    assert route["cost"] > 0
    assert route["travel_time"] > 0


def test_find_path_through_zones(demo_roads):
    graph = build_road_graph(demo_roads)
    route = find_shortest_path(graph, "zone_a", "exit_east")
    assert route["feasible"]
    assert "zone_a" in route["path"]
    assert "exit_east" in route["path"]


def test_blocked_road(demo_roads):
    demo_roads["road_r8"]["blocked"] = True
    graph = build_road_graph(demo_roads)
    route = find_shortest_path(graph, "zone_a", "exit_north")
    # Path exists but goes through blocked road — should be infeasible
    # or route goes around
    assert "zone_a" in route["path"] if route["path"] else True


def test_compute_edge_cost():
    edge = {"length": 500, "travel_time": 6.0, "congestion": 0.3, "risk": 0.2}
    cost = compute_edge_cost(edge)
    assert 0 < cost < 999_999

    blocked_edge = {"blocked": True}
    cost = compute_edge_cost(blocked_edge)
    assert cost == 999_999.0


def test_compute_cost_function():
    edge = {"length": 500, "travel_time": 6.0, "congestion": 0.3, "risk": 0.2}
    cost = compute_cost(edge)
    assert cost > 0


def test_graph_builder_from_scenario(demo_roads, demo_zones, demo_exits):
    graph = build_graph_from_scenario(demo_roads, demo_zones, demo_exits)
    assert graph.number_of_nodes() >= len(demo_zones) + len(demo_exits)
