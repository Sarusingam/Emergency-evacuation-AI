"""
Video Processor — Frame extraction from video/camera.

Handles OpenCV video capture for processing video files or
camera streams. Provides frame-by-frame iteration with optional
frame skipping and resolution limiting.

Input: Video file path or camera index.
Output: Iterator of frames (numpy arrays).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Generator

import numpy as np

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Extracts frames from video files or camera streams.

    Supports:
    - Video file processing (.mp4, .avi, etc.)
    - Camera stream capture
    - Frame skipping for performance
    - Resolution limiting
    """

    def __init__(
        self,
        frame_skip: int = 2,
        max_resolution: int = 1280,
    ) -> None:
        """Initialize the video processor.

        Args:
            frame_skip: Process every Nth frame (1 = all frames).
            max_resolution: Maximum width for processing.
        """
        self.frame_skip = max(1, frame_skip)
        self.max_resolution = max_resolution
        self._cap = None

    def process_video(
        self,
        source: str | int,
        max_frames: int | None = None,
    ) -> Generator[tuple[int, np.ndarray], None, None]:
        """Process frames from a video source.

        Args:
            source: Video file path or camera index (0 for default).
            max_frames: Maximum frames to yield (None = all).

        Yields:
            Tuple of (frame_number, frame_array) for each processed frame.
        """
        try:
            import cv2
        except ImportError:
            logger.warning("OpenCV not available, generating dummy frames")
            yield from self._generate_dummy_frames(max_frames or 30)
            return

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            logger.error("Failed to open video source: %s", source)
            return

        self._cap = cap
        frame_count = 0
        yielded = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # Skip frames
                if frame_count % self.frame_skip != 0:
                    continue

                # Resize if needed
                h, w = frame.shape[:2]
                if w > self.max_resolution:
                    scale = self.max_resolution / w
                    frame = cv2.resize(
                        frame,
                        (int(w * scale), int(h * scale)),
                    )

                yield frame_count, frame
                yielded += 1

                if max_frames and yielded >= max_frames:
                    break

        finally:
            cap.release()
            self._cap = None

        logger.info(
            "Processed %d/%d frames from %s",
            yielded, frame_count, source,
        )

    def get_video_info(self, source: str | int) -> dict[str, Any]:
        """Get information about a video source.

        Args:
            source: Video file path or camera index.

        Returns:
            Dict with fps, frame_count, width, height, duration.
        """
        try:
            import cv2
        except ImportError:
            return {"error": "OpenCV not available"}

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            return {"error": f"Cannot open {source}"}

        info = {
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }
        info["duration"] = (
            info["frame_count"] / info["fps"]
            if info["fps"] > 0 else 0.0
        )
        cap.release()
        return info

    def _generate_dummy_frames(
        self, count: int
    ) -> Generator[tuple[int, np.ndarray], None, None]:
        """Generate dummy frames when OpenCV is unavailable.

        Args:
            count: Number of frames to generate.

        Yields:
            Tuple of (frame_number, random_frame).
        """
        for i in range(1, count + 1):
            frame = np.random.randint(
                0, 255, (720, 1280, 3), dtype=np.uint8
            )
            yield i, frame
