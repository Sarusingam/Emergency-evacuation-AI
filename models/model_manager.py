"""
Model Manager — Load/save model weights.

Handles model weight persistence with graceful error handling
for missing files, version mismatches, etc.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"


class ModelManager:
    """Manages model weight loading and saving.

    Supports:
    - Saving model checkpoints with metadata.
    - Loading weights with error handling.
    - Listing available checkpoints.
    """

    def __init__(self, weights_dir: str | Path | None = None) -> None:
        """Initialize the model manager.

        Args:
            weights_dir: Directory for model weights.
        """
        self.weights_dir = Path(weights_dir) if weights_dir else WEIGHTS_DIR
        self.weights_dir.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        model: Any,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Save model weights.

        Args:
            model: PyTorch model to save.
            name: Checkpoint name (without extension).
            metadata: Optional metadata to save alongside.

        Returns:
            Path to saved checkpoint.
        """
        try:
            import torch
        except ImportError:
            raise RuntimeError("PyTorch required for saving models")

        path = self.weights_dir / f"{name}.pt"
        checkpoint = {
            "model_state_dict": model.state_dict(),
            "metadata": metadata or {},
        }
        torch.save(checkpoint, path)
        logger.info("Model saved to %s", path)
        return path

    def load_model(
        self,
        model: Any,
        name: str,
        strict: bool = True,
    ) -> dict[str, Any]:
        """Load model weights.

        Args:
            model: PyTorch model to load weights into.
            name: Checkpoint name (without extension).
            strict: Whether to strictly enforce matching keys.

        Returns:
            Metadata dict from the checkpoint.

        Raises:
            FileNotFoundError: If checkpoint doesn't exist.
        """
        try:
            import torch
        except ImportError:
            raise RuntimeError("PyTorch required for loading models")

        path = self.weights_dir / f"{name}.pt"
        if not path.exists():
            raise FileNotFoundError(
                f"No checkpoint found at {path}. "
                f"Available: {self.list_checkpoints()}"
            )

        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"], strict=strict)
        logger.info("Model loaded from %s", path)
        return checkpoint.get("metadata", {})

    def list_checkpoints(self) -> list[str]:
        """List available checkpoint names.

        Returns:
            List of checkpoint names (without .pt extension).
        """
        return [
            p.stem for p in sorted(self.weights_dir.glob("*.pt"))
        ]

    def checkpoint_exists(self, name: str) -> bool:
        """Check if a checkpoint exists.

        Args:
            name: Checkpoint name.

        Returns:
            True if checkpoint file exists.
        """
        return (self.weights_dir / f"{name}.pt").exists()
