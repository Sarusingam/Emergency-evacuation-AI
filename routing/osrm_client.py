"""
OSRM Client — Optional real-world routing via OSRM API.

Wraps the OSRM HTTP API for real road routing. Falls back
gracefully when OSRM is not available.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class OSRMClient:
    """HTTP client for the OSRM routing service.

    OSRM (Open Source Routing Machine) provides fast shortest-path
    routing on real road networks. This client is optional — the
    system defaults to NetworkX graph routing if OSRM is unavailable.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        timeout: float = 5.0,
    ) -> None:
        """Initialize the OSRM client.

        Args:
            base_url: OSRM server URL.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if the OSRM server is reachable.

        Returns:
            True if server responds.
        """
        if self._available is not None:
            return self._available

        try:
            import httpx
            response = httpx.get(
                f"{self.base_url}/health",
                timeout=self.timeout,
            )
            self._available = response.status_code == 200
        except Exception:
            self._available = False

        if not self._available:
            logger.info("OSRM not available at %s", self.base_url)

        return self._available

    def get_route(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
    ) -> dict[str, Any] | None:
        """Get a route between two coordinates.

        Args:
            origin: (latitude, longitude) of start.
            destination: (latitude, longitude) of end.

        Returns:
            Route dict with distance, duration, geometry, or None if failed.
        """
        if not self.is_available():
            return None

        try:
            import httpx

            # OSRM expects lon,lat (not lat,lon)
            coords = (
                f"{origin[1]},{origin[0]};"
                f"{destination[1]},{destination[0]}"
            )
            url = f"{self.base_url}/route/v1/driving/{coords}"

            response = httpx.get(
                url,
                params={
                    "overview": "full",
                    "geometries": "geojson",
                    "steps": "true",
                },
                timeout=self.timeout,
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if data.get("code") != "Ok" or not data.get("routes"):
                return None

            route = data["routes"][0]
            return {
                "distance": route.get("distance", 0),
                "duration": route.get("duration", 0),
                "geometry": route.get("geometry", {}),
            }

        except Exception as exc:
            logger.warning("OSRM route request failed: %s", exc)
            return None
