"""
Structured Agent Messages for Inter-Agent Communication.

This module defines the message format that agents use to communicate
with each other through the shared state. Messages are accumulated
in the state's 'messages' list.

Each message has a sender, receiver, type, payload, priority,
and timestamp. Messages use Pydantic models for validation.

Input: Created by agents during their processing phase.
Output: Added to state['messages'] list for other agents to read.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of messages agents can send.

    Each type indicates the purpose/content of the message.
    """
    CROWD_UPDATE = "crowd_update"
    RISK_UPDATE = "risk_update"
    TRAFFIC_UPDATE = "traffic_update"
    TRANSPORT_UPDATE = "transport_update"
    ROUTE_UPDATE = "route_update"
    PLAN_UPDATE = "plan_update"
    ALERT = "alert"
    REPLAN_REQUEST = "replan_request"
    STATUS_REPORT = "status_report"
    COORDINATION = "coordination"
    ACKNOWLEDGMENT = "acknowledgment"


class MessagePriority(str, Enum):
    """Priority levels for agent messages.

    Higher priority messages should be processed first.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentMessage(BaseModel):
    """Structured message for inter-agent communication.

    Agents create these messages to share information, request actions,
    or report status. Messages are validated by Pydantic and stored
    as dicts in the LangGraph state.

    Attributes:
        sender: Name of the sending agent.
        receiver: Name of the receiving agent, or 'all' for broadcast.
        message_type: Category of the message.
        payload: Structured data specific to the message type.
        priority: How urgent this message is.
        timestamp: ISO-format timestamp when the message was created.
        description: Human-readable summary of the message.
    """
    sender: str = Field(..., description="Name of the sending agent")
    receiver: str = Field(
        default="all",
        description="Target agent name, or 'all' for broadcast",
    )
    message_type: MessageType = Field(
        ..., description="Category of this message"
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data payload",
    )
    priority: MessagePriority = Field(
        default=MessagePriority.MEDIUM,
        description="Message priority level",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-format creation timestamp",
    )
    description: str = Field(
        default="",
        description="Human-readable message summary",
    )

    def to_state_dict(self) -> dict[str, Any]:
        """Convert to a plain dict for LangGraph state storage.

        LangGraph state uses plain dicts, not Pydantic models.
        This method serializes the message for state storage.

        Returns:
            Dictionary representation of this message.
        """
        return self.model_dump(mode="json")


def create_message(
    sender: str,
    message_type: MessageType | str,
    payload: dict[str, Any] | None = None,
    receiver: str = "all",
    priority: MessagePriority | str = MessagePriority.MEDIUM,
    description: str = "",
) -> dict[str, Any]:
    """Convenience function to create and serialize an agent message.

    This is the recommended way for agents to create messages,
    as it handles validation, serialization, and logging.

    Args:
        sender: Name of the sending agent.
        message_type: Category of the message.
        payload: Data payload (dict).
        receiver: Target agent or 'all'.
        priority: Message priority.
        description: Human-readable summary.

    Returns:
        Serialized message dict ready for state storage.
    """
    # Convert string enums if needed
    if isinstance(message_type, str):
        message_type = MessageType(message_type)
    if isinstance(priority, str):
        priority = MessagePriority(priority)

    msg = AgentMessage(
        sender=sender,
        receiver=receiver,
        message_type=message_type,
        payload=payload or {},
        priority=priority,
        description=description,
    )

    logger.debug(
        "[%s → %s] %s: %s",
        sender, receiver, message_type.value, description,
    )

    return msg.to_state_dict()


def filter_messages(
    messages: list[dict[str, Any]],
    receiver: str | None = None,
    message_type: MessageType | str | None = None,
    sender: str | None = None,
    min_priority: MessagePriority | str | None = None,
) -> list[dict[str, Any]]:
    """Filter messages from the state by criteria.

    Useful for agents that need to read only messages relevant
    to them from the accumulated message list.

    Args:
        messages: Full list of messages from state.
        receiver: Filter by target receiver (includes 'all').
        message_type: Filter by message type.
        sender: Filter by sender agent.
        min_priority: Only include messages at or above this priority.

    Returns:
        Filtered list of message dicts.
    """
    priority_order = {
        MessagePriority.LOW.value: 0,
        MessagePriority.MEDIUM.value: 1,
        MessagePriority.HIGH.value: 2,
        MessagePriority.CRITICAL.value: 3,
    }

    if isinstance(message_type, MessageType):
        message_type = message_type.value
    if isinstance(min_priority, MessagePriority):
        min_priority = min_priority.value

    min_priority_val = priority_order.get(min_priority, 0) if min_priority else 0

    result: list[dict[str, Any]] = []
    for msg in messages:
        # Check receiver (include 'all' broadcasts)
        if receiver and msg.get("receiver") not in (receiver, "all"):
            continue
        # Check message type
        if message_type and msg.get("message_type") != message_type:
            continue
        # Check sender
        if sender and msg.get("sender") != sender:
            continue
        # Check priority
        msg_priority_val = priority_order.get(
            msg.get("priority", "medium"), 0
        )
        if msg_priority_val < min_priority_val:
            continue

        result.append(msg)

    return result
