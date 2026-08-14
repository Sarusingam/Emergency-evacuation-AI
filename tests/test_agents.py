"""Tests for the agent system."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.agent_state import create_initial_state, EvacuationState
from agents.agent_messages import (
    create_message, filter_messages, MessageType, MessagePriority,
)
from agents.crowd_agent import CrowdAgent
from agents.risk_agent import RiskAgent
from agents.traffic_agent import TrafficAgent
from agents.transport_agent import TransportAgent


def test_create_initial_state():
    state = create_initial_state(emergency_id="test_001", emergency_type="fire")
    assert state["emergency_id"] == "test_001"
    assert state["emergency_type"] == "fire"
    assert state["emergency_status"] == "active"
    assert state["messages"] == []
    assert state["simulation_step"] == 0


def test_create_message():
    msg = create_message(
        sender="crowd_agent", message_type=MessageType.CROWD_UPDATE,
        payload={"count": 100}, priority=MessagePriority.HIGH,
        description="Test message",
    )
    assert msg["sender"] == "crowd_agent"
    assert msg["message_type"] == "crowd_update"
    assert msg["priority"] == "high"
    assert msg["payload"]["count"] == 100


def test_filter_messages():
    msgs = [
        create_message("a", MessageType.CROWD_UPDATE, priority=MessagePriority.LOW),
        create_message("b", MessageType.ALERT, priority=MessagePriority.CRITICAL),
        create_message("a", MessageType.RISK_UPDATE, priority=MessagePriority.MEDIUM),
    ]
    filtered = filter_messages(msgs, sender="a")
    assert len(filtered) == 2
    filtered = filter_messages(msgs, message_type=MessageType.ALERT)
    assert len(filtered) == 1
    filtered = filter_messages(msgs, min_priority=MessagePriority.HIGH)
    assert len(filtered) == 1


def test_crowd_agent(demo_zones):
    agent = CrowdAgent()
    state = create_initial_state(zones=demo_zones)
    result = agent.process(state)
    assert "crowd_analysis" in result
    assert "messages" in result
    zones = result["crowd_analysis"]["zones"]
    assert "zone_a" in zones
    assert zones["zone_a"]["count"] == 800


def test_risk_agent(demo_zones, demo_roads, demo_exits):
    agent = RiskAgent()
    state = create_initial_state(
        zones=demo_zones, roads=demo_roads, exits=demo_exits,
        emergency_type="chemical_spill",
    )
    # Run crowd agent first to populate crowd_analysis
    crowd = CrowdAgent()
    state.update(crowd.process(state))
    result = agent.process(state)
    assert "risk_assessment" in result
    risk_zones = result["risk_assessment"]["zones"]
    assert "zone_d" in risk_zones
    assert risk_zones["zone_d"]["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_traffic_agent(demo_roads):
    agent = TrafficAgent()
    state = create_initial_state(roads=demo_roads)
    result = agent.process(state)
    assert "traffic_status" in result
    roads = result["traffic_status"]["roads"]
    assert len(roads) == len(demo_roads)


def test_transport_agent(demo_zones, demo_vehicles):
    agent = TransportAgent()
    state = create_initial_state(zones=demo_zones, vehicles=demo_vehicles)
    # Need crowd + risk data
    crowd = CrowdAgent()
    state.update(crowd.process(state))
    risk = RiskAgent()
    state.update(risk.process(state))
    result = agent.process(state)
    assert "transport_status" in result
