"""
People Counter — Counts people from detections.

Provides simple detection-based counting and density-weighted
counting for more accurate crowd estimates.

Input: List of Detection objects from the detector.
Output: Count of people and optional density-weighted count.
"""

from __future__ import annotations

import logging
from typing import Any

from computer_vision.detector import Detection

logger = logging.getLogger(__name__)


class PeopleCounter:
    """Counts people from detection results.

    Supports two modes:
    1. Simple count: number of detections above threshold.
    2. Density-weighted: adjusts count by detection overlap/density.
    """

    def __init__(self, confidence_threshold: float = 0.3) -> None:
        """Initialize the counter.

        Args:
            confidence_threshold: Minimum confidence to count.
        """
        self.confidence_threshold = confidence_threshold

    def count(self, detections: list[Detection]) -> dict[str, Any]:
        """Count people from detections.

        Args:
            detections: List of Detection objects.

        Returns:
            Dict with 'count', 'high_confidence_count',
            'average_confidence', and 'density_adjusted_count'.
        """
        filtered = [
            d for d in detections
            if d.confidence >= self.confidence_threshold
        ]
        high_conf = [d for d in filtered if d.confidence >= 0.7]

        avg_conf = (
            sum(d.confidence for d in filtered) / len(filtered)
            if filtered else 0.0
        )

        # Density-weighted count: adjust for overlapping detections
        density_count = self._density_adjusted_count(filtered)

        return {
            "count": len(filtered),
            "high_confidence_count": len(high_conf),
            "average_confidence": round(avg_conf, 3),
            "density_adjusted_count": density_count,
        }

    def _density_adjusted_count(
        self, detections: list[Detection]
    ) -> int:
        """Adjust count based on detection density/overlap.

        In dense crowds, detections may overlap significantly.
        This method uses IoU-based deduplication to get a more
        accurate count.

        Args:
            detections: Filtered detections.

        Returns:
            Adjusted people count.
        """
        if len(detections) <= 1:
            return len(detections)

        # Simple non-maximum suppression by overlap
        kept: list[Detection] = []
        sorted_dets = sorted(
            detections, key=lambda d: d.confidence, reverse=True
        )

        for det in sorted_dets:
            is_duplicate = False
            for kept_det in kept:
                iou = self._compute_iou(det.bbox, kept_det.bbox)
                if iou > 0.5:
                    is_duplicate = True
                    break
            if not is_duplicate:
                kept.append(det)

        return len(kept)

    @staticmethod
    def _compute_iou(
        box1: tuple[float, ...],
        box2: tuple[float, ...],
    ) -> float:
        """Compute Intersection over Union of two boxes.

        Args:
            box1: (x1, y1, x2, y2).
            box2: (x1, y1, x2, y2).

        Returns:
            IoU value (0-1).
        """
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
        area2 = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0
