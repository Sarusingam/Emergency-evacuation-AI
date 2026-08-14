"""
Redis Event Bus — Redis pub/sub implementation.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Callable

logger = logging.getLogger(__name__)


class RedisEventBus:
    """Redis-based event bus using pub/sub.

    Falls back gracefully if Redis is not available.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0",
                 channel_prefix: str = "evacuation") -> None:
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self._client = None
        self._pubsub = None
        self._thread: threading.Thread | None = None
        self._callbacks: dict[str, list[Callable]] = {}
        self._connect()

    def _connect(self) -> None:
        try:
            import redis
            self._client = redis.from_url(self.redis_url)
            self._client.ping()
            self._pubsub = self._client.pubsub()
            logger.info("Connected to Redis at %s", self.redis_url)
        except Exception as e:
            logger.warning("Redis not available: %s", e)
            self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def _full_channel(self, channel: str) -> str:
        return f"{self.channel_prefix}:{channel}"

    def publish(self, channel: str, message: dict[str, Any]) -> None:
        if not self._client:
            return
        try:
            self._client.publish(self._full_channel(channel), json.dumps(message))
        except Exception as e:
            logger.error("Redis publish error: %s", e)

    def subscribe(self, channel: str, callback: Callable[[dict[str, Any]], None]) -> None:
        if not self._pubsub:
            return
        full = self._full_channel(channel)
        self._callbacks.setdefault(full, []).append(callback)

        def handler(msg):
            if msg["type"] == "message":
                data = json.loads(msg["data"])
                for cb in self._callbacks.get(full, []):
                    try:
                        cb(data)
                    except Exception as e:
                        logger.error("Callback error: %s", e)

        self._pubsub.subscribe(**{full: handler})
        if not self._thread or not self._thread.is_alive():
            self._thread = self._pubsub.run_in_thread(sleep_time=0.1, daemon=True)

    def unsubscribe(self, channel: str) -> None:
        if self._pubsub:
            self._pubsub.unsubscribe(self._full_channel(channel))
        self._callbacks.pop(self._full_channel(channel), None)
