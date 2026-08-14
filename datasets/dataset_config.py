"""
Dataset Configuration — Paths, splits, and parameters.

Central configuration for all supported crowd counting datasets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Base data directory
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Dataset configurations
DATASET_CONFIGS: dict[str, dict[str, Any]] = {
    "dronecrowd": {
        "name": "DroneCrowd",
        "description": "Drone-captured crowd counting dataset",
        "raw_dir": RAW_DIR / "DroneCrowd",
        "processed_dir": PROCESSED_DIR / "dronecrowd",
        "image_size": (640, 640),
        "train_split": 0.8,
        "val_split": 0.1,
        "test_split": 0.1,
        "download_url": None,  # Requires manual download
    },
    "nwpu": {
        "name": "NWPU-Crowd",
        "description": "Large-scale crowd counting benchmark",
        "raw_dir": RAW_DIR / "NWPU-Crowd",
        "processed_dir": PROCESSED_DIR / "nwpu",
        "image_size": (576, 768),
        "train_split": 0.7,
        "val_split": 0.15,
        "test_split": 0.15,
        "download_url": None,
    },
    "ucf_qnrf": {
        "name": "UCF-QNRF",
        "description": "Ultra-high density crowd counting dataset",
        "raw_dir": RAW_DIR / "UCF-QNRF",
        "processed_dir": PROCESSED_DIR / "ucf_qnrf",
        "image_size": (576, 768),
        "train_split": 0.8,
        "val_split": 0.0,
        "test_split": 0.2,
        "download_url": None,
    },
}


def get_dataset_config(name: str) -> dict[str, Any]:
    """Get configuration for a specific dataset.

    Args:
        name: Dataset name (dronecrowd, nwpu, ucf_qnrf).

    Returns:
        Configuration dict.

    Raises:
        ValueError: If dataset name is unknown.
    """
    config = DATASET_CONFIGS.get(name.lower())
    if not config:
        available = ", ".join(DATASET_CONFIGS.keys())
        raise ValueError(
            f"Unknown dataset '{name}'. Available: {available}"
        )
    return config
