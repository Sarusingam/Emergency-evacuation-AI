"""
Coordinator Agent — Emergency Orchestration.

This agent is the central decision-maker that reviews all agent
outputs and produces the final evacuation plan. It can use an LLM
for reasoning/explanation or fall back to a rule-based engine.

IMPORTANT:
- The LLM ONLY reasons about strategy and generates explanations.
- All numerical route calculations are done by tools (NetworkX).
- In demo mode (no API key), the rule-based engine is used.

Input: All agent outputs in the state.
Output: state['evacuation_plan'] with the final approved plan,
        state['coordinator_reasoning'] with explanation.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent
from agents.agent_messages import MessagePriority, MessageType, filter_messages

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """Agent responsible for orchestrating the evacuation.

    Reviews outputs from all other agents (crowd, risk, traffic,
    transport, route) and produces a final evacuation plan with
    reasoning. Decides whether replanning is needed based on
    alerts and condition changes.

    Supports two modes:
    1. LLM mode: Uses an LLM to reason about the plan.
    2. Rule-based mode: Uses deterministic rules (demo default).
    """

    def __init__(self) -> None:
        """Initialize the Coordinator Agent."""
        super().__init__(
            name="coordinator_agent",
            description="Orchestrates evacuation by reviewing all agent outputs",
        )
        self._use_llm = False
        self._llm = None

    def _try_init_llm(self) -> bool:
        """Attempt to initialize the LLM for reasoning.

        Returns:
            True if LLM was initialized, False for rule-based mode.
        """
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            logger.info("No LLM API key found, using rule-based coordinator")
            return False

        try:
            from langchain_openai import ChatOpenAI
            from agents.tools import COORDINATOR_TOOLS, set_tool_context

            self._llm = ChatOpenAI(
                model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
                temperature=0.2,
                max_tokens=1024,
            ).bind_tools(COORDINATOR_TOOLS)
            self._set_tool_context = set_tool_context
            logger.info("LLM coordinator initialized")
            return True
        except Exception as exc:
            logger.warning("Failed to init LLM: %s. Using rule-based.", exc)
            return False

    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Produce the final evacuation plan.

        Steps:
            1. Review all agent outputs.
            2. Check for alerts and replan triggers.
            3. Generate reasoning (LLM or rule-based).
            4. Approve/modify the evacuation plan.
            5. Decide if replanning is needed.

        Args:
            state: The full EvacuationState dict.

        Returns:
            State update with 'evacuation_plan', 'coordinator_reasoning',
            and control flow flags.
        """
        self._log_action("processing", "Reviewing all agent outputs")

        # Try LLM on first call
        if self._llm is None and not self._use_llm:
            self._use_llm = self._try_init_llm()

        # Gather all agent outputs
        crowd = state.get("crowd_analysis", {})
        risk = state.get("risk_assessment", {})
        traffic = state.get("traffic_status", {})
        transport = state.get("transport_status", {})
        routes = state.get("evacuation_routes", {})
        messages = state.get("messages", [])
        replan_count = state.get("replan_count", 0)
        max_replans = state.get("max_replan_cycles", 10)

        # Generate plan using rule-based engine (or LLM)
        if self._use_llm and self._llm:
            plan, reasoning = self._llm_plan(state)
        else:
            plan, reasoning = self._rule_based_plan(
                crowd, risk, traffic, transport, routes, messages,
                state,
            )

        # Check if we need to replan
        needs_replan = state.get("needs_replan", False)
        replan_reason = state.get("replan_reason", "")

        # Also check alerts in messages for replan triggers
        critical_alerts = filter_messages(
            messages,
            message_type=MessageType.ALERT,
            min_priority=MessagePriority.CRITICAL,
        )
        if critical_alerts and replan_count < max_replans:
            latest_alert = critical_alerts[-1]
            alert_type = latest_alert.get("payload", {}).get("alert_type", "")
            if alert_type in ("road_blocked", "no_feasible_route"):
                needs_replan = True
                replan_reason = f"Critical alert: {alert_type}"

        # Cap replanning
        if replan_count >= max_replans:
            needs_replan = False
            replan_reason = f"Max replan cycles ({max_replans}) reached"
            reasoning += f"\n\nReplanning capped at {max_replans} cycles."

        # Build messages
        out_messages: list[dict[str, Any]] = []
        out_messages.append(
            self._create_message(
                message_type=MessageType.PLAN_UPDATE,
                payload={
                    "status": plan.get("status", "approved"),
                    "total_people": plan.get("total_people", 0),
                    "estimated_time": plan.get("estimated_total_time", 0),
                    "needs_replan": needs_replan,
                },
                priority=MessagePriority.HIGH,
                description=f"Evacuation plan {'approved' if not needs_replan else 'needs replanning'}",
            )
        )

        self._log_action(
            "completed",
            f"Plan status: {plan.get('status', 'unknown')}, replan: {needs_replan}",
        )

        result: dict[str, Any] = {
            "evacuation_plan": plan,
            "coordinator_reasoning": reasoning,
            "messages": out_messages,
            "last_updated": self._now_iso(),
        }

        if needs_replan:
            result["needs_replan"] = True
            result["replan_reason"] = replan_reason
            result["replan_count"] = replan_count + 1

        return result

    def _rule_based_plan(
        self,
        crowd: dict[str, Any],
        risk: dict[str, Any],
        traffic: dict[str, Any],
        transport: dict[str, Any],
        routes: dict[str, Any],
        messages: list[dict],
        state: dict[str, Any],
    ) -> tuple[dict[str, Any], str]:
        """Generate an evacuation plan using deterministic rules.

        This is the default mode (no LLM needed).

        Args:
            crowd: Crowd analysis output.
            risk: Risk assessment output.
            traffic: Traffic status output.
            transport: Transport status output.
            routes: Evacuation routes output.
            messages: All agent messages.
            state: Full state.

        Returns:
            Tuple of (plan dict, reasoning string).
        """
        # Extract key data
        route_assignments = routes.get("assignments", {})
        route_summary = routes.get("summary", {})
        risk_summary = risk.get("summary", {})
        traffic_summary = traffic.get("summary", {})
        crowd_summary = crowd.get("summary", {})

        total_people = route_summary.get("total_people", 0)
        assigned = route_summary.get("people_assigned", 0)
        unassigned = route_summary.get("unassigned", 0)
        max_travel = route_summary.get("max_travel_time", 0.0)
        blocked_roads = traffic_summary.get("blocked_roads", [])
        critical_zones = risk_summary.get("critical_zones", [])

        # Build the plan
        plan = {
            "status": "approved",
            "assignments": route_assignments,
            "total_people": total_people,
            "people_assigned": assigned,
            "people_unassigned": unassigned,
            "estimated_total_time": max_travel,
            "blocked_roads": blocked_roads,
            "critical_zones": critical_zones,
            "plan_id": f"plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "timestamp": self._now_iso(),
        }

        # If there are unassigned people, mark plan as partial
        if unassigned > 0:
            plan["status"] = "partial"

        # Generate reasoning
        reasoning_lines = [
            "## Evacuation Plan Assessment",
            "",
            f"**Total people:** {total_people}",
            f"**Assigned to routes:** {assigned}",
            f"**Unassigned:** {unassigned}",
            f"**Estimated max travel time:** {max_travel:.1f} minutes",
            "",
        ]

        if critical_zones:
            reasoning_lines.append(
                f"⚠️ **Critical zones:** {', '.join(critical_zones)} — "
                "prioritizing evacuation from these zones."
            )

        if blocked_roads:
            reasoning_lines.append(
                f"🚧 **Blocked roads:** {', '.join(blocked_roads)} — "
                "routes have been recalculated to avoid these."
            )

        if unassigned > 0:
            reasoning_lines.append(
                f"⚠️ **{unassigned} people unassigned** — "
                "exit capacity may be insufficient. Consider opening "
                "additional exits or increasing capacity."
            )
        else:
            reasoning_lines.append(
                "✅ All evacuees have been assigned routes."
            )

        # Transport summary
        transport_summary = transport.get("summary", {})
        if transport_summary:
            reasoning_lines.extend([
                "",
                f"**Vehicles dispatched:** {transport_summary.get('dispatched', 0)}",
                f"**Vehicles available:** {transport_summary.get('available', 0)}",
            ])

        reasoning = "\n".join(reasoning_lines)
        return plan, reasoning

    def _llm_plan(
        self, state: dict[str, Any]
    ) -> tuple[dict[str, Any], str]:
        """Generate plan using LLM reasoning.

        The LLM reviews a summary of all agent outputs and produces
        strategic reasoning. All numerical data comes from the
        deterministic tools, not the LLM.

        Args:
            state: Full state dict.

        Returns:
            Tuple of (plan dict, reasoning string).
        """
        try:
            from agents.tools import set_tool_context
            set_tool_context(state)

            # Build prompt with current situation summary
            prompt = self._build_llm_prompt(state)

            # Invoke LLM
            response = self._llm.invoke(prompt)
            reasoning = response.content if hasattr(response, "content") else str(response)

            # Use the route agent's assignments as the plan
            # (LLM provides reasoning, not numerical data)
            routes = state.get("evacuation_routes", {})
            plan = {
                "status": "approved",
                "assignments": routes.get("assignments", {}),
                "total_people": routes.get("summary", {}).get("total_people", 0),
                "people_assigned": routes.get("summary", {}).get("people_assigned", 0),
                "people_unassigned": routes.get("summary", {}).get("unassigned", 0),
                "estimated_total_time": routes.get("summary", {}).get("max_travel_time", 0),
                "plan_id": f"plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "timestamp": self._now_iso(),
                "llm_enhanced": True,
            }

            return plan, reasoning

        except Exception as exc:
            logger.warning("LLM plan failed: %s. Falling back to rules.", exc)
            # Fallback to rule-based
            return self._rule_based_plan(
                state.get("crowd_analysis", {}),
                state.get("risk_assessment", {}),
                state.get("traffic_status", {}),
                state.get("transport_status", {}),
                state.get("evacuation_routes", {}),
                state.get("messages", []),
                state,
            )

    def _build_llm_prompt(self, state: dict[str, Any]) -> str:
        """Build a prompt summarizing the situation for the LLM.

        Args:
            state: Full state dict.

        Returns:
            Formatted prompt string.
        """
        routes = state.get("evacuation_routes", {})
        risk = state.get("risk_assessment", {})
        traffic = state.get("traffic_status", {})
        crowd = state.get("crowd_analysis", {})

        prompt = (
            "You are an emergency evacuation coordinator AI. Review the "
            "current situation and provide strategic reasoning for the "
            "evacuation plan. All routes have already been computed by "
            "the optimization engine — your job is to validate the plan "
            "and explain the strategy.\n\n"
            f"Emergency type: {state.get('emergency_type', 'unknown')}\n"
            f"Severity: {state.get('emergency_severity', 'unknown')}\n\n"
            f"Crowd summary: {json.dumps(crowd.get('summary', {}), indent=2)}\n\n"
            f"Risk summary: {json.dumps(risk.get('summary', {}), indent=2)}\n\n"
            f"Traffic summary: {json.dumps(traffic.get('summary', {}), indent=2)}\n\n"
            f"Route summary: {json.dumps(routes.get('summary', {}), indent=2)}\n\n"
            "Provide a brief strategic assessment (3-5 bullet points) "
            "covering: priorities, risks, and recommendations."
        )
        return prompt
