"""Tests for simulation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulation.scenario_manager import ScenarioManager
from simulation.crowd_simulator import CrowdSimulator
from simulation.traffic_simulator import TrafficSimulator
from simulation.evacuation_simulator import EvacuationSimulator
from simulation.fallback_simulator import FallbackSimulator


def test_scenario_manager():
    sm = ScenarioManager()
    data = sm.get_scenario_state_data("default_demo")
    assert "zones" in data
    assert "roads" in data
    assert "exits" in data
    assert "vehicles" in data
    assert len(data["zones"]) == 6
    assert len(data["exits"]) == 4


def test_crowd_simulator(demo_zones):
    sim = CrowdSimulator()
    assigns = {"zone_a": [{"people": 100}]}
    updated = sim.simulate_step(demo_zones, assigns)
    assert updated["zone_a"]["crowd_count"] <= 800


def test_traffic_simulator(demo_roads):
    sim = TrafficSimulator()
    assigns = {}
    updated = sim.simulate_step(demo_roads, assigns)
    assert len(updated) == len(demo_roads)


def test_traffic_block_unblock(demo_roads):
    sim = TrafficSimulator()
    roads = sim.block_road(demo_roads, "road_r1")
    assert roads["road_r1"]["blocked"] is True
    roads = sim.unblock_road(roads, "road_r1", 0.4)
    assert roads["road_r1"]["blocked"] is False
    assert roads["road_r1"]["congestion"] == 0.4


def test_evacuation_simulator(demo_zones):
    sim = EvacuationSimulator()
    sim.initialize(demo_zones)
    assert sim.initial_population == 4500
    snap = sim.record_step(demo_zones)
    assert snap["step"] == 1
    assert snap["progress"] == 0.0


def test_fallback_simulator():
    sim = FallbackSimulator()
    data = sim.initialize("default_demo")
    assert len(data["zones"]) == 6
    result = sim.step()
    assert result["step"] == 1
    assert sim.is_running
