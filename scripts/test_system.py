"""
End-to-End System Test — Validates the entire system pipeline.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import traceback


def run_test(name, fn):
    try:
        fn()
        print(f"  ✅ {name}")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        traceback.print_exc()
        return False


def test_config():
    from simulation.scenario_manager import ScenarioManager
    sm = ScenarioManager()
    data = sm.get_scenario_state_data("default_demo")
    assert len(data["zones"]) == 6
    assert len(data["roads"]) == 12
    assert len(data["exits"]) == 4


def test_agents():
    from agents.agent_state import create_initial_state
    from agents.crowd_agent import CrowdAgent
    from agents.risk_agent import RiskAgent
    from agents.traffic_agent import TrafficAgent
    from agents.transport_agent import TransportAgent
    from agents.route_agent import RouteAgent
    from agents.coordinator_agent import CoordinatorAgent
    from simulation.scenario_manager import ScenarioManager

    sm = ScenarioManager()
    data = sm.get_scenario_state_data("default_demo")
    state = create_initial_state(
        emergency_id="test", emergency_type="fire", zones=data["zones"],
        roads=data["roads"], exits=data["exits"], vehicles=data["vehicles"],
    )

    for AgentClass in [CrowdAgent, RiskAgent, TrafficAgent, TransportAgent, RouteAgent, CoordinatorAgent]:
        agent = AgentClass()
        result = agent.process(state)
        state.update(result)
        assert isinstance(result, dict)


def test_graph():
    from agents.agent_state import create_initial_state
    from agents.graph import create_runnable_graph
    from simulation.scenario_manager import ScenarioManager

    sm = ScenarioManager()
    data = sm.get_scenario_state_data("default_demo")
    state = create_initial_state(
        emergency_id="test", emergency_type="fire", zones=data["zones"],
        roads=data["roads"], exits=data["exits"], vehicles=data["vehicles"],
    )

    graph = create_runnable_graph()
    result = graph.invoke(state)
    assert "evacuation_plan" in result
    assert result["evacuation_plan"].get("status") in ("approved", "partial")


def test_simulation():
    from simulation.fallback_simulator import FallbackSimulator
    sim = FallbackSimulator()
    sim.initialize("default_demo")
    for _ in range(5):
        sim.step()
    summary = sim.get_summary()
    assert summary["steps_completed"] == 5


def test_cv_pipeline():
    import numpy as np
    from computer_vision.inference import CVInferencePipeline
    pipeline = CVInferencePipeline(demo_mode=True)
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    result = pipeline.process_frame(frame)
    assert result["frame_number"] == 1
    assert len(result["detections"]) > 0


def test_database():
    from database.database import db_manager
    db_manager.db_url = "sqlite:///./data/test_system.db"
    db_manager.initialize()
    db_manager.create_tables()
    session = next(db_manager.get_session())
    session.close()
    # Dispose engine to release SQLite file lock (critical on Windows)
    db_manager.dispose()
    import os
    if os.path.exists("./data/test_system.db"):
        os.remove("./data/test_system.db")


def test_user_api():
    from backend.services.emergency_service import emergency_service
    emergency_service.start_emergency(
        emergency_type="chemical_spill", severity="high", scenario="default_demo"
    )
    user_route = emergency_service.get_user_route("zone_z1")
    assert user_route["emergency_active"] is True
    assert user_route["zone_id"] == "zone_z1"
    assert "route_summary" in user_route

    # Test route change on road block
    v1 = user_route["route_version"]
    emergency_service.block_road("road_r4")
    emergency_service.step_simulation()
    updated = emergency_service.get_user_route("zone_z1")
    assert updated["route_version"] > v1

    # Test map data endpoint returns live geometry and blocked roads for Hyderabad
    map_data = emergency_service.get_user_map_data("zone_z1")
    assert map_data["emergency_active"] is True
    assert map_data["user_zone"]["id"] == "zone_z1"
    assert len(map_data["route_coords"]) > 0
    assert len(map_data["blocked_segments"]) > 0
    assert len(map_data["all_zones"]) == 6


def main():
    print("\n" + "=" * 50)
    print("  🧪 End-to-End System Test")
    print("=" * 50 + "\n")

    tests = [
        ("Config & Scenario Loading", test_config),
        ("Agent Pipeline (Sequential)", test_agents),
        ("LangGraph Workflow", test_graph),
        ("Fallback Simulation", test_simulation),
        ("CV Pipeline (Demo Mode)", test_cv_pipeline),
        ("Database (SQLite)", test_database),
        ("User API & Replanning", test_user_api),
    ]

    passed = sum(run_test(name, fn) for name, fn in tests)
    total = len(tests)

    print(f"\n{'=' * 50}")
    print(f"  Results: {passed}/{total} passed")
    print(f"{'=' * 50}\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
