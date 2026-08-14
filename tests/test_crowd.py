"""Tests for computer vision pipeline."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from computer_vision.detector import PersonDetector, Detection
from computer_vision.counter import PeopleCounter
from computer_vision.tracker import CentroidTracker
from computer_vision.density import DensityEstimator
from computer_vision.inference import CVInferencePipeline


def test_detector_demo_mode():
    detector = PersonDetector(demo_mode=True)
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    detections = detector.detect(frame)
    assert len(detections) > 0
    assert all(isinstance(d, Detection) for d in detections)
    assert all(d.confidence > 0 for d in detections)


def test_detection_to_dict():
    det = Detection(bbox=(10, 20, 50, 80), confidence=0.95)
    d = det.to_dict()
    assert d["bbox"] == [10, 20, 50, 80]
    assert d["confidence"] == 0.95
    assert d["center"] == [30.0, 50.0]


def test_counter():
    counter = PeopleCounter(confidence_threshold=0.3)
    detections = [
        Detection((10, 10, 50, 50), 0.9),
        Detection((100, 100, 150, 150), 0.8),
        Detection((200, 200, 250, 250), 0.1),  # Below threshold
    ]
    result = counter.count(detections)
    assert result["count"] == 2
    assert result["high_confidence_count"] == 2


def test_tracker():
    tracker = CentroidTracker(max_disappeared=5)
    dets1 = [Detection((10, 10, 30, 30), 0.9), Detection((100, 100, 120, 120), 0.9)]
    tracked = tracker.update(dets1)
    assert len(tracked) == 2
    # Second frame, slightly moved
    dets2 = [Detection((12, 12, 32, 32), 0.9), Detection((102, 102, 122, 122), 0.9)]
    tracked = tracker.update(dets2)
    assert len(tracked) == 2
    assert tracker.total_tracked == 2


def test_density_estimator():
    estimator = DensityEstimator(grid_rows=5, grid_cols=5)
    detections = [Detection((100, 100, 120, 120), 0.9) for _ in range(10)]
    result = estimator.estimate(detections, 1280, 720)
    assert result["total_count"] == 10
    assert len(result["density_grid"]) == 5
    assert result["max_density"] > 0


def test_pipeline():
    pipeline = CVInferencePipeline(demo_mode=True)
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    result = pipeline.process_frame(frame)
    assert "detections" in result
    assert "count" in result
    assert "tracks" in result
    assert "density" in result
    assert result["frame_number"] == 1
