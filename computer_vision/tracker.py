"""
Simple Centroid Tracker — Tracks detected persons across frames.

Uses centroid distance matching to associate detections across
consecutive frames. Provides unique IDs for each tracked person.

Input: Detections per frame from the detector.
Output: Tracked objects with persistent IDs.
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any

import numpy as np

from computer_vision.detector import Detection

logger = logging.getLogger(__name__)


class CentroidTracker:
    """Simple centroid-based multi-object tracker.

    Associates detections across frames based on distance between
    centroids. Deregisters objects that disappear for too many frames.
    """

    def __init__(
        self,
        max_disappeared: int = 30,
        max_distance: float = 80.0,
    ) -> None:
        """Initialize the tracker.

        Args:
            max_disappeared: Frames before deregistering a lost object.
            max_distance: Maximum distance to match centroids.
        """
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self._next_id = 0
        self._objects: OrderedDict[int, np.ndarray] = OrderedDict()
        self._disappeared: dict[int, int] = {}
        self._total_tracked = 0

    @property
    def active_count(self) -> int:
        """Number of currently tracked objects."""
        return len(self._objects)

    @property
    def total_tracked(self) -> int:
        """Total unique objects tracked since init."""
        return self._total_tracked

    def update(
        self, detections: list[Detection]
    ) -> dict[int, tuple[float, float]]:
        """Update tracker with new detections.

        Args:
            detections: Current frame's detections.

        Returns:
            Dict of object_id -> centroid (cx, cy).
        """
        if not detections:
            # Mark all objects as disappeared
            for obj_id in list(self._disappeared.keys()):
                self._disappeared[obj_id] += 1
                if self._disappeared[obj_id] > self.max_disappeared:
                    self._deregister(obj_id)
            return {
                oid: (float(c[0]), float(c[1]))
                for oid, c in self._objects.items()
            }

        # Extract centroids from detections
        input_centroids = np.array(
            [det.center for det in detections], dtype=float
        )

        # If no existing objects, register all
        if len(self._objects) == 0:
            for centroid in input_centroids:
                self._register(centroid)
        else:
            self._match_and_update(input_centroids)

        return {
            oid: (float(c[0]), float(c[1]))
            for oid, c in self._objects.items()
        }

    def _register(self, centroid: np.ndarray) -> int:
        """Register a new tracked object.

        Args:
            centroid: Object centroid coordinates.

        Returns:
            Assigned object ID.
        """
        obj_id = self._next_id
        self._objects[obj_id] = centroid
        self._disappeared[obj_id] = 0
        self._next_id += 1
        self._total_tracked += 1
        return obj_id

    def _deregister(self, obj_id: int) -> None:
        """Remove a tracked object.

        Args:
            obj_id: Object ID to remove.
        """
        del self._objects[obj_id]
        del self._disappeared[obj_id]

    def _match_and_update(self, input_centroids: np.ndarray) -> None:
        """Match existing objects to new detections.

        Uses distance matrix to find optimal assignment.

        Args:
            input_centroids: Centroids from current frame.
        """
        obj_ids = list(self._objects.keys())
        obj_centroids = np.array(list(self._objects.values()))

        # Compute distance matrix
        dist_matrix = np.linalg.norm(
            obj_centroids[:, np.newaxis] - input_centroids[np.newaxis, :],
            axis=2,
        )

        # Greedy matching: closest pairs first
        rows = dist_matrix.min(axis=1).argsort()
        cols = dist_matrix.argmin(axis=1)[rows]

        used_rows: set[int] = set()
        used_cols: set[int] = set()

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            if dist_matrix[row, col] > self.max_distance:
                continue

            obj_id = obj_ids[row]
            self._objects[obj_id] = input_centroids[col]
            self._disappeared[obj_id] = 0

            used_rows.add(row)
            used_cols.add(col)

        # Handle unmatched existing objects
        unused_rows = set(range(len(obj_ids))) - used_rows
        for row in unused_rows:
            obj_id = obj_ids[row]
            self._disappeared[obj_id] += 1
            if self._disappeared[obj_id] > self.max_disappeared:
                self._deregister(obj_id)

        # Register new detections
        unused_cols = set(range(len(input_centroids))) - used_cols
        for col in unused_cols:
            self._register(input_centroids[col])

    def get_tracks(self) -> list[dict[str, Any]]:
        """Get all active tracks.

        Returns:
            List of track dicts with id, centroid, disappeared count.
        """
        return [
            {
                "id": oid,
                "centroid": (float(c[0]), float(c[1])),
                "disappeared": self._disappeared.get(oid, 0),
            }
            for oid, c in self._objects.items()
        ]
