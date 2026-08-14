"""
LangGraph Workflow — Agent Orchestration Graph.

This module defines the LangGraph StateGraph that orchestrates the
multi-agent evacuation workflow. Each agent is a node, and edges
define the processing order with conditional branches for replanning.

Workflow:
    crowd_agent → risk_agent → traffic_agent → transport_agent
        → route_agent → coordinator_agent
        → (conditional) → either END or loop back for replanning

The graph supports dynamic replanning: if the coordinator or traffic
agent detects that conditions have changed (blocked road, density
spike, capacity overflow), the workflow loops back to re-analyze.

Input: EvacuationState initialized from scenario data.
Output: Fully processed state with evacuation plan.
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from agents.agent_state import EvacuationState
from agents.crowd_agent import CrowdAgent
from agents.risk_agent import RiskAgent
from agents.traffic_agent import TrafficAgent
from agents.transport_agent import TransportAgent
from agents.route_agent import RouteAgent
from agents.coordinator_agent import CoordinatorAgent

logger = logging.getLogger(__name__)

# ── Singleton agent instances ───────────────────────────────────
# Created once, reused across workflow invocations.
_crowd_agent = CrowdAgent()
_risk_agent = RiskAgent()
_traffic_agent = TrafficAgent()
_transport_agent = TransportAgent()
_route_agent = RouteAgent()
_coordinator_agent = CoordinatorAgent()


# ================================================================
# NODE FUNCTIONS
# ================================================================
# Each function is a LangGraph node that delegates to an agent
# class instance. The function receives the full state and returns
# a partial state update dict.
# ================================================================


def crowd_node(state: EvacuationState) -> dict[str, Any]:
    """LangGraph node for crowd analysis.

    Args:
        state: Current evacuation state.

    Returns:
        Partial state update from the CrowdAgent.
    """
    logger.info("=== Crowd Agent Node ===")
    return _crowd_agent.process(state)


def risk_node(state: EvacuationState) -> dict[str, Any]:
    """LangGraph node for risk assessment.

    Args:
        state: Current evacuation state.

    Returns:
        Partial state update from the RiskAgent.
    """
    logger.info("=== Risk Agent Node ===")
    return _risk_agent.process(state)


def traffic_node(state: EvacuationState) -> dict[str, Any]:
    """LangGraph node for traffic monitoring.

    Args:
        state: Current evacuation state.

    Returns:
        Partial state update from the TrafficAgent.
    """
    logger.info("=== Traffic Agent Node ===")
    return _traffic_agent.process(state)


def transport_node(state: EvacuationState) -> dict[str, Any]:
    """LangGraph node for vehicle management.

    Args:
        state: Current evacuation state.

    Returns:
        Partial state update from the TransportAgent.
    """
    logger.info("=== Transport Agent Node ===")
    return _transport_agent.process(state)


def route_node(state: EvacuationState) -> dict[str, Any]:
    """LangGraph node for route optimization.

    Args:
        state: Current evacuation state.

    Returns:
        Partial state update from the RouteAgent.
    """
    logger.info("=== Route Agent Node ===")
    return _route_agent.process(state)


def coordinator_node(state: EvacuationState) -> dict[str, Any]:
    """LangGraph node for the coordinator (final decision-maker).

    Args:
        state: Current evacuation state.

    Returns:
        Partial state update from the CoordinatorAgent.
    """
    logger.info("=== Coordinator Agent Node ===")
    return _coordinator_agent.process(state)


# ================================================================
# CONDITIONAL EDGES
# ================================================================


def should_replan(state: EvacuationState) -> str:
    """Decide whether to replan or finish.

    Called after the coordinator node to determine the next step.
    If replanning is needed AND we haven't exceeded the max cycle
    count, loop back to crowd_agent for a fresh analysis.

    Args:
        state: Current evacuation state.

    Returns:
        'replan' to loop back, or 'end' to finish.
    """
    needs_replan = state.get("needs_replan", False)
    replan_count = state.get("replan_count", 0)
    max_cycles = state.get("max_replan_cycles", 10)

    if needs_replan and replan_count < max_cycles:
        logger.info(
            "Replanning triggered (cycle %d/%d): %s",
            replan_count, max_cycles,
            state.get("replan_reason", "unknown"),
        )
        return "replan"
    else:
        if replan_count >= max_cycles:
            logger.warning("Max replan cycles reached (%d)", max_cycles)
        logger.info("Workflow complete — no replanning needed")
        return "end"


# ================================================================
# GRAPH BUILDER
# ================================================================


def build_evacuation_graph() -> StateGraph:
    """Build the LangGraph StateGraph for evacuation.

    Graph structure:
        START → crowd_agent → risk_agent → traffic_agent
            → transport_agent → route_agent → coordinator_agent
            → (conditional: replan → crowd_agent, end → END)

    Returns:
        Compiled LangGraph StateGraph ready to invoke.
    """
    logger.info("Building evacuation agent graph...")

    # Create the state graph
    graph = StateGraph(EvacuationState)

    # Add nodes
    graph.add_node("crowd_agent", crowd_node)
    graph.add_node("risk_agent", risk_node)
    graph.add_node("traffic_agent", traffic_node)
    graph.add_node("transport_agent", transport_node)
    graph.add_node("route_agent", route_node)
    graph.add_node("coordinator_agent", coordinator_node)

    # Add edges (linear pipeline)
    graph.set_entry_point("crowd_agent")
    graph.add_edge("crowd_agent", "risk_agent")
    graph.add_edge("risk_agent", "traffic_agent")
    graph.add_edge("traffic_agent", "transport_agent")
    graph.add_edge("transport_agent", "route_agent")
    graph.add_edge("route_agent", "coordinator_agent")

    # Conditional edge after coordinator
    graph.add_conditional_edges(
        "coordinator_agent",
        should_replan,
        {
            "replan": "crowd_agent",   # Loop back for replanning
            "end": END,                # Finish
        },
    )

    logger.info("Evacuation graph built successfully")
    return graph


def create_runnable_graph():
    """Create a compiled, runnable graph.

    Returns:
        Compiled LangGraph app that can be invoked with
        app.invoke(initial_state).
    """
    graph = build_evacuation_graph()
    return graph.compile()
