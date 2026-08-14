"""
Abstract Base Agent for the Evacuation System.

This module defines the BaseAgent abstract class that all agents
inherit from. It provides a common interface (observe → analyze → act)
and shared utilities like logging and message creation.

Each concrete agent implements the `process()` method, which receives
the full LangGraph state and returns a dict of state updates.

Input: LangGraph EvacuationState dict.
Output: Dict of state field updates to merge back into the state.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from agents.agent_messages import (
    MessagePriority,
    MessageType,
    create_message,
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all evacuation agents.

    Provides:
    - Common constructor with name and description.
    - Abstract `process()` method for LangGraph node integration.
    - Helper methods for logging, message creation, and timestamps.

    Subclasses must implement `process(state) -> dict` which takes
    the full EvacuationState and returns a partial state update.

    Example:
        class MyAgent(BaseAgent):
            def __init__(self):
                super().__init__("my_agent", "Does something useful")

            def process(self, state):
                result = self._do_work(state)
                return {"my_output": result}
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize the agent.

        Args:
            name: Unique agent identifier (e.g., 'crowd_agent').
            description: Human-readable description of what the agent does.
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agents.{name}")

    @abstractmethod
    def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Process the current state and return updates.

        This is the main entry point called by the LangGraph node
        function. The agent reads relevant fields from state,
        performs its analysis, and returns a dict of fields to update.

        Args:
            state: The full EvacuationState dict.

        Returns:
            Dict of state field updates. Only include fields that
            this agent modifies. The 'messages' field should be a
            list of message dicts (they accumulate via operator.add).
        """
        ...

    def _create_message(
        self,
        message_type: MessageType | str,
        payload: dict[str, Any] | None = None,
        receiver: str = "all",
        priority: MessagePriority | str = MessagePriority.MEDIUM,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a structured agent message.

        Convenience wrapper around create_message() that automatically
        sets this agent as the sender.

        Args:
            message_type: Category of the message.
            payload: Data payload dict.
            receiver: Target agent or 'all' for broadcast.
            priority: Message priority level.
            description: Human-readable summary.

        Returns:
            Serialized message dict for state storage.
        """
        return create_message(
            sender=self.name,
            message_type=message_type,
            payload=payload,
            receiver=receiver,
            priority=priority,
            description=description,
        )

    def _log_action(self, action: str, details: str = "") -> None:
        """Log an agent action with consistent formatting.

        Args:
            action: Short action description (e.g., 'analyzed zones').
            details: Additional details to include in the log.
        """
        msg = f"[{self.name}] {action}"
        if details:
            msg += f" | {details}"
        self.logger.info(msg)

    def _log_warning(self, warning: str, details: str = "") -> None:
        """Log a warning with consistent formatting.

        Args:
            warning: Warning description.
            details: Additional details.
        """
        msg = f"[{self.name}] WARNING: {warning}"
        if details:
            msg += f" | {details}"
        self.logger.warning(msg)

    @staticmethod
    def _now_iso() -> str:
        """Get current UTC timestamp in ISO format.

        Returns:
            ISO-format timestamp string.
        """
        return datetime.now(timezone.utc).isoformat()
