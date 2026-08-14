"""
NWPU-Crowd Dataset Loader.

Loads the NWPU-Crowd benchmark dataset for crowd counting.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from datasets.dataset_config import get_dataset_config

logger = logging.getLogger(__name__)


class NWPUCrowdLoader:
    """Loader for the NWPU-Crowd dataset.

    Expected structure:
        NWPU-Crowd/
        ├── images/
        ├── jsons/       (point annotations)
        └── train.txt / val.txt / test.txt
    """

    def __init__(self, root_dir: str | Path | None = None) -> None:
        config = get_dataset_config("nwpu")
        self.root_dir = Path(root_dir) if root_dir else config["raw_dir"]
        self.config = config

    def is_available(self) -> bool:
        return self.root_dir.exists() and any(self.root_dir.iterdir())

    def load_split(self, split: str = "train") -> list[dict[str, Any]]:
        if not self.is_available():
            raise FileNotFoundError(
                f"NWPU-Crowd dataset not found at {self.root_dir}. "
                f"Please download and extract it there."
            )

        split_file = self.root_dir / f"{split}.txt"
        image_dir = self.root_dir / "images"

        if split_file.exists():
            ids = split_file.read_text().strip().split("\n")
        elif image_dir.exists():
            ids = [p.stem for p in sorted(image_dir.glob("*.jpg"))]
        else:
            return []

        samples: list[dict[str, Any]] = []
        for img_id in ids:
            img_id = img_id.strip()
            if not img_id:
                continue
            img_path = image_dir / f"{img_id}.jpg"
            ann_path = self.root_dir / "jsons" / f"{img_id}.json"
            samples.append({
                "image_path": str(img_path),
                "annotation_path": str(ann_path) if ann_path.exists() else None,
                "split": split,
                "dataset": "nwpu",
            })

        logger.info("Loaded %d NWPU %s samples", len(samples), split)
        return samples

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.config["name"],
            "description": self.config["description"],
            "available": self.is_available(),
            "root_dir": str(self.root_dir),
        }
