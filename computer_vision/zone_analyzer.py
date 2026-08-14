"""
Zone Analyzer — Maps detections to predefined zones.

Assigns person detections to geographic zones based on their
position within the camera frame. Uses zone definitions (bounding
regions) to determine which zone each detection belongs to.

Input: Detections + zone definitions (pixel-space or geo-projected).
Output: Per-zone counts and density metrics.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from computer_vision.detector import Detection

logger = logging.getLogger(__name__)


class ZoneAnalyzer:
    """Maps detections to predefined zones.

    In a real deployment, zones would be defined by geographic
    coordinates projected into the camera frame. In demo mode,
    zones are defined as rectangular regions in pixel space.
    """

    def __init__(
        self,
        zones: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the zone analyzer.

        Args:
            zones: List of zone dicts with 'id', 'name', and either
                   'bbox' (x1,y1,x2,y2 in pixels) or 'center'+'radius'.
        """
        self.zones = zones or []

    def set_zones_from_scenario(
        self,
        scenario_zones: dict[str, dict[str, Any]],
        frame_width: int = 1280,
        frame_height: int = 720,
    ) -> None:
        """Create pixel-space zones from scenario data.

        Maps scenario zones (lat/lon) to pixel regions in the
        frame for demo purposes.

        Args:
            scenario_zones: Zone data from the scenario.
            frame_width: Frame width for pixel mapping.
            frame_height: Frame height for pixel mapping.
        """
        n = len(scenario_zones)
        if n == 0:
            return

        # Simple grid layout for demo
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        cell_w = frame_width / cols
        cell_h = frame_height / rows

        self.zones = []
        for i, (zone_id, zone_data) in enumerate(scenario_zones.items()):
            row = i // cols
            col = i % cols
            self.zones.append({
                "id": zone_id,
                "name": zone_data.get("name", zone_id),
                "bbox": (
                    col * cell_w,
                    row * cell_h,
                    (col + 1) * cell_w,
                    (row + 1) * cell_h,
                ),
            })

    def analyze(
        self, detections: list[Detection]
    ) -> dict[str, dict[str, Any]]:
        """Assign detections to zones and compute per-zone counts.

        Args:
            detections: List of person detections.

        Returns:
            Dict of zone_id -> {count, density, detections}.
        """
        zone_counts: dict[str, list[Detection]] = {
            z["id"]: [] for z in self.zones
        }

        for det in detections:
            cx, cy = det.center
            for zone_def in self.zones:
                bbox = zone_def.get("bbox")
                if bbox and self._point_in_bbox(cx, cy, bbox):
                    zone_counts[zone_def["id"]].append(det)
                    break  # Assign to first matching zone

        result: dict[str, dict[str, Any]] = {}
        for zone_def in self.zones:
            zone_id = zone_def["id"]
            dets = zone_counts[zone_id]
            bbox = zone_def.get("bbox", (0, 0, 100, 100))
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

            result[zone_id] = {
                "zone_id": zone_id,
                "name": zone_def.get("name", zone_id),
                "count": len(dets),
                "density": round(len(dets) / max(area, 1.0) * 10000, 3),
                "average_confidence": round(
                    sum(d.confidence for d in dets) / max(len(dets), 1), 3
                ),
            }

        return result

    @staticmethod
    def _point_in_bbox(
        x: float, y: float,
        bbox: tuple[float, float, float, float],
    ) -> bool:
        """Check if a point is inside a bounding box.

        Args:
            x: Point x coordinate.
            y: Point y coordinate.
            bbox: (x1, y1, x2, y2).

        Returns:
            True if point is inside bbox.
        """
        return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]
