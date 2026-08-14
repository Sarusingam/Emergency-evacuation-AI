"""
DroneCrowd Dataset Loader.

Loads the DroneCrowd dataset for crowd counting training.
Validates paths and provides clear error messages when data
is not found.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from datasets.dataset_config import get_dataset_config

logger = logging.getLogger(__name__)


class DroneCrowdLoader:
    """Loader for the DroneCrowd dataset.

    Expected directory structure:
        DroneCrowd/
        ├── train/
        │   ├── images/
        │   └── annotations/
        └── test/
            ├── images/
            └── annotations/
    """

    def __init__(self, root_dir: str | Path | None = None) -> None:
        """Initialize the loader.

        Args:
            root_dir: Override path to dataset root. Uses config default if None.
        """
        config = get_dataset_config("dronecrowd")
        self.root_dir = Path(root_dir) if root_dir else config["raw_dir"]
        self.config = config

    def is_available(self) -> bool:
        """Check if the dataset exists at the expected path.

        Returns:
            True if dataset directory exists and has content.
        """
        return self.root_dir.exists() and any(self.root_dir.iterdir())

    def load_split(self, split: str = "train") -> list[dict[str, Any]]:
        """Load a dataset split.

        Args:
            split: One of 'train', 'test'.

        Returns:
            List of sample dicts with 'image_path' and 'annotation_path'.

        Raises:
            FileNotFoundError: If dataset is not found.
        """
        if not self.is_available():
            raise FileNotFoundError(
                f"DroneCrowd dataset not found at {self.root_dir}. "
                f"Please download it and place it in {self.root_dir}"
            )

        split_dir = self.root_dir / split
        image_dir = split_dir / "images"

        if not image_dir.exists():
            logger.warning("No images directory at %s", image_dir)
            return []

        samples: list[dict[str, Any]] = []
        for img_path in sorted(image_dir.glob("*.jpg")):
            ann_path = split_dir / "annotations" / f"{img_path.stem}.txt"
            samples.append({
                "image_path": str(img_path),
                "annotation_path": str(ann_path) if ann_path.exists() else None,
                "split": split,
                "dataset": "dronecrowd",
            })

        logger.info(
            "Loaded %d DroneCrowd %s samples from %s",
            len(samples), split, self.root_dir,
        )
        return samples

    def get_info(self) -> dict[str, Any]:
        """Get dataset information.

        Returns:
            Dict with dataset metadata.
        """
        return {
            "name": self.config["name"],
            "description": self.config["description"],
            "available": self.is_available(),
            "root_dir": str(self.root_dir),
            "image_size": self.config["image_size"],
        }
