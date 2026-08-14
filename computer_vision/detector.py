"""
Person Detector — YOLO-based detection with demo fallback.

This module handles person detection from images/frames using
the Ultralytics YOLO model. When YOLO weights are unavailable
or in demo mode, it generates synthetic detections.

Input: Image frame (numpy array, H×W×3 BGR).
Output: List of detection dicts with bounding boxes and confidence.
"""

from __future__ import annotations

import logging
import random
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class Detection:
    """A single person detection.

    Attributes:
        bbox: Bounding box as (x1, y1, x2, y2) in pixels.
        confidence: Detection confidence score (0-1).
        class_id: COCO class ID (0 for person).
        center: Center point (cx, cy).
    """

    __slots__ = ("bbox", "confidence", "class_id", "center")

    def __init__(
        self,
        bbox: tuple[float, float, float, float],
        confidence: float = 0.9,
        class_id: int = 0,
    ) -> None:
        self.bbox = bbox
        self.confidence = confidence
        self.class_id = class_id
        self.center = (
            (bbox[0] + bbox[2]) / 2.0,
            (bbox[1] + bbox[3]) / 2.0,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "bbox": list(self.bbox),
            "confidence": round(self.confidence, 3),
            "class_id": self.class_id,
            "center": list(self.center),
        }

    @property
    def area(self) -> float:
        """Bounding box area in pixels."""
        return max(0, self.bbox[2] - self.bbox[0]) * max(0, self.bbox[3] - self.bbox[1])


class PersonDetector:
    """YOLO-based person detector with demo fallback.

    Attempts to load a YOLO model on initialization. If unavailable,
    automatically falls back to generating synthetic detections.
    """

    def __init__(
        self,
        model_name: str = "yolov8n",
        confidence_threshold: float = 0.3,
        person_class_id: int = 0,
        demo_mode: bool = True,
    ) -> None:
        """Initialize the detector.

        Args:
            model_name: YOLO model variant name.
            confidence_threshold: Minimum confidence to keep detection.
            person_class_id: COCO class ID for person.
            demo_mode: If True, skip YOLO loading and use synthetic.
        """
        self.confidence_threshold = confidence_threshold
        self.person_class_id = person_class_id
        self.demo_mode = demo_mode
        self._model = None

        if not demo_mode:
            self._try_load_model(model_name)
        else:
            logger.info("PersonDetector running in demo mode (synthetic)")

    def _try_load_model(self, model_name: str) -> None:
        """Attempt to load the YOLO model.

        Args:
            model_name: Model variant to load.
        """
        try:
            from ultralytics import YOLO
            self._model = YOLO(f"{model_name}.pt")
            logger.info("Loaded YOLO model: %s", model_name)
        except Exception as exc:
            logger.warning(
                "Failed to load YOLO model '%s': %s. Using demo fallback.",
                model_name, exc,
            )
            self.demo_mode = True

    def detect(
        self,
        frame: np.ndarray,
        roi: tuple[int, int, int, int] | None = None,
    ) -> list[Detection]:
        """Detect persons in a frame.

        Args:
            frame: BGR image as numpy array (H×W×3).
            roi: Optional region of interest (x1, y1, x2, y2).

        Returns:
            List of Detection objects for detected persons.
        """
        if self.demo_mode or self._model is None:
            return self._generate_synthetic_detections(frame, roi)

        return self._run_yolo(frame, roi)

    def _run_yolo(
        self,
        frame: np.ndarray,
        roi: tuple[int, int, int, int] | None = None,
    ) -> list[Detection]:
        """Run YOLO inference on a frame.

        Args:
            frame: Input image.
            roi: Optional crop region.

        Returns:
            List of person detections.
        """
        if roi:
            x1, y1, x2, y2 = roi
            crop = frame[y1:y2, x1:x2]
        else:
            crop = frame
            x1, y1 = 0, 0

        results = self._model(crop, verbose=False)
        detections: list[Detection] = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls = int(box.cls[0]) if box.cls is not None else -1
                conf = float(box.conf[0]) if box.conf is not None else 0.0

                if cls != self.person_class_id:
                    continue
                if conf < self.confidence_threshold:
                    continue

                xyxy = box.xyxy[0].cpu().numpy()
                det = Detection(
                    bbox=(
                        float(xyxy[0]) + x1,
                        float(xyxy[1]) + y1,
                        float(xyxy[2]) + x1,
                        float(xyxy[3]) + y1,
                    ),
                    confidence=conf,
                    class_id=cls,
                )
                detections.append(det)

        logger.debug("YOLO detected %d persons", len(detections))
        return detections

    def _generate_synthetic_detections(
        self,
        frame: np.ndarray,
        roi: tuple[int, int, int, int] | None = None,
    ) -> list[Detection]:
        """Generate synthetic person detections for demo mode.

        Creates realistic-looking detections distributed across
        the frame to simulate crowd detection.

        Args:
            frame: Input image (used for dimensions).
            roi: Optional region of interest.

        Returns:
            List of synthetic detections.
        """
        h, w = frame.shape[:2]
        if roi:
            x1, y1, x2, y2 = roi
            w_roi, h_roi = x2 - x1, y2 - y1
        else:
            x1, y1 = 0, 0
            w_roi, h_roi = w, h

        # Generate 10-50 synthetic detections
        n_detections = random.randint(10, 50)
        detections: list[Detection] = []

        for _ in range(n_detections):
            # Random person-sized bounding box
            pw = random.randint(20, 40)
            ph = random.randint(50, 100)

            cx = random.randint(x1 + pw, x1 + w_roi - pw)
            cy = random.randint(y1 + ph // 2, y1 + h_roi - ph // 2)

            det = Detection(
                bbox=(
                    float(cx - pw // 2),
                    float(cy - ph // 2),
                    float(cx + pw // 2),
                    float(cy + ph // 2),
                ),
                confidence=round(random.uniform(0.5, 0.98), 3),
                class_id=0,
            )
            detections.append(det)

        return detections
