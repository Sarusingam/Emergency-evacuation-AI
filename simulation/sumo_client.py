"""
SUMO Client — Optional SUMO/TraCI interface (no-op if SUMO unavailable).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SUMOClient:
    """Optional wrapper for SUMO traffic simulation via TraCI.

    Falls back to no-op methods when SUMO is not installed.
    """

    def __init__(self, config_file: str | None = None) -> None:
        self.config_file = config_file
        self._connected = False
        self._available = self._check_available()

    def _check_available(self) -> bool:
        try:
            import traci  # noqa: F401
            return True
        except ImportError:
            logger.info("SUMO/TraCI not available — using fallback simulator")
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    def connect(self) -> bool:
        if not self._available or not self.config_file:
            return False
        try:
            import traci
            traci.start(["sumo", "-c", self.config_file])
            self._connected = True
            return True
        except Exception as e:
            logger.warning("SUMO connection failed: %s", e)
            return False

    def step(self) -> dict[str, Any]:
        if not self._connected:
            return {}
        try:
            import traci
            traci.simulationStep()
            return {"time": traci.simulation.getTime()}
        except Exception:
            return {}

    def close(self) -> None:
        if self._connected:
            try:
                import traci
                traci.close()
            except Exception:
                pass
            self._connected = False
