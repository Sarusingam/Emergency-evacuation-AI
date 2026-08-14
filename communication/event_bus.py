"""
Event Bus — Abstract event bus protocol.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol


class EventBus(Protocol):
    """Abstract event bus interface.

    Implementations: LocalEventBus (in-memory), RedisEventBus (Redis pub/sub).
    """

    def publish(self, channel: str, message: dict[str, Any]) -> None:
        """Publish a message to a channel."""
        ...

    def subscribe(self, channel: str, callback: Callable[[dict[str, Any]], None]) -> None:
        """Subscribe to a channel with a callback."""
        ...

    def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel."""
        ...
