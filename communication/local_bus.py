"""
Local Event Bus — In-memory event bus (default in demo mode).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)


class LocalEventBus:
    """In-process event bus using simple callback registration.

    Default implementation when Redis is not available.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._history: list[dict[str, Any]] = []

    def publish(self, channel: str, message: dict[str, Any]) -> None:
        """Publish a message to all subscribers of a channel."""
        self._history.append({"channel": channel, "message": message})
        for callback in self._subscribers.get(channel, []):
            try:
                callback(message)
            except Exception as e:
                logger.error("Subscriber error on '%s': %s", channel, e)

    def subscribe(self, channel: str, callback: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback for a channel."""
        self._subscribers[channel].append(callback)

    def unsubscribe(self, channel: str) -> None:
        """Remove all subscribers from a channel."""
        self._subscribers.pop(channel, None)

    def get_history(self, channel: str | None = None, limit: int = 100) -> list[dict]:
        """Get recent messages, optionally filtered by channel."""
        if channel:
            return [m for m in self._history if m["channel"] == channel][-limit:]
        return self._history[-limit:]
