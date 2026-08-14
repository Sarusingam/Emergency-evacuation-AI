"""
Density Estimation — Grid-based crowd density from detections.

Divides the frame into a grid and computes density (people per
cell) for heatmap visualization and zone-level density analysis.

Input: List of Detection objects and frame dimensions.
Output: 2D density grid (numpy array) and summary stats.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from computer_vision.detector import Detection

logger = logging.getLogger(__name__)


class DensityEstimator:
    """Grid-based crowd density estimator.

    Divides the image into a grid and counts detections per cell
    to produce a density map suitable for heatmap rendering.
    """

    def __init__(
        self,
        grid_rows: int = 10,
        grid_cols: int = 10,
    ) -> None:
        """Initialize the density estimator.

        Args:
            grid_rows: Number of rows in the density grid.
            grid_cols: Number of columns in the density grid.
        """
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols

    def estimate(
        self,
        detections: list[Detection],
        frame_width: int,
        frame_height: int,
    ) -> dict[str, Any]:
        """Estimate density from detections.

        Args:
            detections: Person detections.
            frame_width: Image width in pixels.
            frame_height: Image height in pixels.

        Returns:
            Dict with 'density_grid' (2D list), 'max_density',
            'avg_density', 'total_count', and 'hotspots'.
        """
        grid = np.zeros((self.grid_rows, self.grid_cols), dtype=float)
        cell_w = frame_width / self.grid_cols
        cell_h = frame_height / self.grid_rows

        # Count detections per grid cell
        for det in detections:
            cx, cy = det.center
            col = min(int(cx / cell_w), self.grid_cols - 1)
            row = min(int(cy / cell_h), self.grid_rows - 1)
            col = max(0, col)
            row = max(0, row)
            grid[row, col] += 1.0

        # Normalize by cell area (in m² equivalent)
        # Assuming each cell covers approx cell_w * cell_h pixels
        # A rough conversion: 1 pixel ≈ 0.05m at typical camera height
        pixel_to_meter = 0.05
        cell_area_m2 = (cell_w * pixel_to_meter) * (cell_h * pixel_to_meter)
        density_grid = grid / max(cell_area_m2, 0.01)

        # Find hotspots (cells above threshold)
        hotspots: list[dict[str, Any]] = []
        avg_density = float(density_grid.mean())
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                if density_grid[r, c] > avg_density * 2.0 and grid[r, c] > 0:
                    hotspots.append({
                        "row": r,
                        "col": c,
                        "density": round(float(density_grid[r, c]), 3),
                        "count": int(grid[r, c]),
                    })

        return {
            "density_grid": density_grid.tolist(),
            "count_grid": grid.astype(int).tolist(),
            "max_density": round(float(density_grid.max()), 3),
            "avg_density": round(avg_density, 3),
            "total_count": len(detections),
            "hotspots": hotspots,
            "grid_shape": [self.grid_rows, self.grid_cols],
        }
