"""
Run Demo — Execute a complete demo evacuation scenario.

Runs the agent workflow and simulates evacuation step by step.
"""

import sys
import time
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("demo")

    print("\n" + "=" * 60)
    print("  🚨 Emergency Evacuation AI — Demo Scenario")
    print("=" * 60 + "\n")

    # Initialize
    from agents.agent_state import create_initial_state
    from agents.graph import create_runnable_graph
    from simulation.fallback_simulator import FallbackSimulator
    from simulation.scenario_manager import ScenarioManager

    sm = ScenarioManager()
    data = sm.get_scenario_state_data("default_demo")

    print(f"📍 Loaded scenario: default_demo")
    print(f"   Zones: {len(data['zones'])}")
    print(f"   Roads: {len(data['roads'])}")
    print(f"   Exits: {len(data['exits'])}")
    print(f"   Vehicles: {len(data['vehicles'])}")

    total_pop = sum(z.get("crowd_count", 0) for z in data["zones"].values())
    print(f"   Total population: {total_pop}")

    # Create initial state
    state = create_initial_state(
        emergency_id="demo_001",
        emergency_type="chemical_spill",
        emergency_severity="high",
        zones=data["zones"],
        roads=data["roads"],
        exits=data["exits"],
        vehicles=data["vehicles"],
    )

    # Run agent workflow
    print("\n🤖 Running Agent Workflow...")
    print("-" * 40)

    try:
        graph = create_runnable_graph()
        result = graph.invoke(state)
        state.update(result)
        print("✅ Agent workflow completed!")
    except Exception as e:
        print(f"⚠️ Agent workflow error: {e}")
        print("   Continuing with default state...")

    # Print plan
    plan = state.get("evacuation_plan", {})
    reasoning = state.get("coordinator_reasoning", "")

    print(f"\n📋 Evacuation Plan: {plan.get('status', 'unknown')}")
    print(f"   People: {plan.get('total_people', 0)}")
    print(f"   Assigned: {plan.get('people_assigned', 0)}")
    print(f"   Unassigned: {plan.get('people_unassigned', 0)}")

    if reasoning:
        print(f"\n💭 Coordinator Reasoning:")
        for line in reasoning.split("\n")[:10]:
            print(f"   {line}")

    # Run simulation
    print("\n🏃 Running Evacuation Simulation...")
    print("-" * 40)

    sim = FallbackSimulator()
    sim.initialize("default_demo")
    assignments = plan.get("assignments", {})

    for step in range(1, 51):
        result = sim.step(assignments)
        snap = result.get("snapshot", {})
        progress = snap.get("progress", 0) * 100

        bar_len = 30
        filled = int(bar_len * progress / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"   Step {step:3d}: [{bar}] {progress:5.1f}% — {snap.get('current_population', 0)} remaining")

        if result.get("events_triggered"):
            for evt in result["events_triggered"]:
                print(f"   ⚡ Event: {evt.get('description', evt.get('type', 'unknown'))}")

        if result.get("is_complete"):
            print(f"\n✅ Evacuation complete at step {step}!")
            break

        time.sleep(0.05)

    # Summary
    summary = sim.get_summary()
    print("\n" + "=" * 60)
    print("  📊 Final Summary")
    print("=" * 60)
    print(f"   Initial Population: {summary.get('initial_population', 0)}")
    print(f"   Evacuated:          {summary.get('evacuated', 0)}")
    print(f"   Progress:           {summary.get('progress', 0) * 100:.1f}%")
    print(f"   Steps:              {summary.get('steps_completed', 0)}")
    print(f"   Complete:           {'✅ Yes' if summary.get('is_complete') else '❌ No'}")
    print()


if __name__ == "__main__":
    main()
