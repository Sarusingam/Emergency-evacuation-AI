"""
UCF-QNRF Dataset Loader.

Loads the UCF-QNRF ultra-high density crowd counting dataset.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from datasets.dataset_config import get_dataset_config

logger = logging.getLogger(__name__)


class UCFQNRFLoader:
    """Loader for the UCF-QNRF dataset.

    Expected structure:
        UCF-QNRF/
        ├── Train/
        │   ├── img_0001.jpg
        │   ├── img_0001_ann.mat
        │   └── ...
        └── Test/
            ├── img_0001.jpg
            └── ...
    """

    def __init__(self, root_dir: str | Path | None = None) -> None:
        config = get_dataset_config("ucf_qnrf")
        self.root_dir = Path(root_dir) if root_dir else config["raw_dir"]
        self.config = config

    def is_available(self) -> bool:
        return self.root_dir.exists() and any(self.root_dir.iterdir())

    def load_split(self, split: str = "train") -> list[dict[str, Any]]:
        if not self.is_available():
            raise FileNotFoundError(
                f"UCF-QNRF dataset not found at {self.root_dir}. "
                f"Please download and extract it there."
            )

        split_dir = self.root_dir / ("Train" if split == "train" else "Test")
        if not split_dir.exists():
            return []

        samples: list[dict[str, Any]] = []
        for img_path in sorted(split_dir.glob("img_*.jpg")):
            ann_path = split_dir / f"{img_path.stem}_ann.mat"
            samples.append({
                "image_path": str(img_path),
                "annotation_path": str(ann_path) if ann_path.exists() else None,
                "split": split,
                "dataset": "ucf_qnrf",
            })

        logger.info("Loaded %d UCF-QNRF %s samples", len(samples), split)
        return samples

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.config["name"],
            "description": self.config["description"],
            "available": self.is_available(),
            "root_dir": str(self.root_dir),
        }
