"""
CV Inference Pipeline — Full computer vision orchestrator.

Chains together detector → counter → tracker → density → zone_analyzer
into a single pipeline that processes frames end-to-end.

Input: Video source or individual frames.
Output: Per-zone crowd counts and density analysis.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from computer_vision.counter import PeopleCounter
from computer_vision.density import DensityEstimator
from computer_vision.detector import PersonDetector
from computer_vision.tracker import CentroidTracker
from computer_vision.zone_analyzer import ZoneAnalyzer

logger = logging.getLogger(__name__)


class CVInferencePipeline:
    """Full computer vision pipeline for crowd analysis.

    Orchestrates: detection → counting → tracking → density → zone analysis.
    Can process individual frames or full video streams.
    """

    def __init__(
        self,
        demo_mode: bool = True,
        yolo_model: str = "yolov8n",
        confidence_threshold: float = 0.3,
    ) -> None:
        """Initialize the full CV pipeline.

        Args:
            demo_mode: Use synthetic detections instead of YOLO.
            yolo_model: YOLO model variant.
            confidence_threshold: Detection confidence threshold.
        """
        self.detector = PersonDetector(
            model_name=yolo_model,
            confidence_threshold=confidence_threshold,
            demo_mode=demo_mode,
        )
        self.counter = PeopleCounter(
            confidence_threshold=confidence_threshold,
        )
        self.tracker = CentroidTracker()
        self.density_estimator = DensityEstimator()
        self.zone_analyzer = ZoneAnalyzer()
        self._frame_count = 0

        logger.info(
            "CV pipeline initialized (demo_mode=%s, model=%s)",
            demo_mode, yolo_model,
        )

    def setup_zones(
        self,
        scenario_zones: dict[str, dict[str, Any]],
        frame_width: int = 1280,
        frame_height: int = 720,
    ) -> None:
        """Configure zones from scenario data.

        Args:
            scenario_zones: Zone definitions from the scenario.
            frame_width: Frame width for zone mapping.
            frame_height: Frame height for zone mapping.
        """
        self.zone_analyzer.set_zones_from_scenario(
            scenario_zones, frame_width, frame_height
        )
        logger.info("Zones configured: %d zones", len(scenario_zones))

    def process_frame(
        self,
        frame: np.ndarray,
    ) -> dict[str, Any]:
        """Process a single frame through the full pipeline.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Dict with detections, counts, tracks, density, zones.
        """
        self._frame_count += 1
        h, w = frame.shape[:2]

        # 1. Detect
        detections = self.detector.detect(frame)

        # 2. Count
        count_result = self.counter.count(detections)

        # 3. Track
        tracked = self.tracker.update(detections)

        # 4. Density
        density_result = self.density_estimator.estimate(
            detections, w, h
        )

        # 5. Zone analysis
        zone_result = self.zone_analyzer.analyze(detections)

        return {
            "frame_number": self._frame_count,
            "detections": [d.to_dict() for d in detections],
            "count": count_result,
            "tracks": {
                "active": len(tracked),
                "total_tracked": self.tracker.total_tracked,
                "positions": {
                    str(k): list(v) for k, v in tracked.items()
                },
            },
            "density": density_result,
            "zones": zone_result,
        }

    def get_zone_summary(self) -> dict[str, Any]:
        """Get the latest zone analysis summary.

        Returns:
            Summary dict with per-zone counts.
        """
        return {
            "frame_count": self._frame_count,
            "active_tracks": self.tracker.active_count,
            "total_tracked": self.tracker.total_tracked,
        }
