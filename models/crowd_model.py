"""
Crowd Counting CNN — Simple crowd density estimation model.

A lightweight CNN that predicts crowd density maps from images.
Designed for training on DroneCrowd/NWPU-Crowd/UCF-QNRF datasets.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.info("PyTorch not available — crowd model is disabled")


if TORCH_AVAILABLE:

    class CrowdCountingCNN(nn.Module):
        """Simple CNN for crowd density map prediction.

        Architecture:
            - 4 conv blocks with batch norm and ReLU
            - Progressive downsampling then upsampling
            - Final 1×1 conv for density map output
        """

        def __init__(self, in_channels: int = 3) -> None:
            """Initialize the model.

            Args:
                in_channels: Number of input channels (3 for RGB).
            """
            super().__init__()

            # Encoder
            self.conv1 = nn.Sequential(
                nn.Conv2d(in_channels, 64, 3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
            )
            self.conv2 = nn.Sequential(
                nn.Conv2d(64, 128, 3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
            )
            self.conv3 = nn.Sequential(
                nn.Conv2d(128, 128, 3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
            )
            self.conv4 = nn.Sequential(
                nn.Conv2d(128, 64, 3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
            )

            # Density map output
            self.output = nn.Conv2d(64, 1, 1)

            self.pool = nn.MaxPool2d(2, 2)
            self.upsample = nn.Upsample(
                scale_factor=2, mode="bilinear", align_corners=True
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """Forward pass.

            Args:
                x: Input tensor (B, C, H, W).

            Returns:
                Density map tensor (B, 1, H, W).
            """
            x1 = self.conv1(x)
            x2 = self.pool(x1)
            x2 = self.conv2(x2)
            x3 = self.pool(x2)
            x3 = self.conv3(x3)
            x4 = self.upsample(x3)
            x4 = self.conv4(x4)
            x5 = self.upsample(x4)
            out = self.output(x5)
            return F.relu(out)

else:
    # Stub class when PyTorch is not installed
    class CrowdCountingCNN:  # type: ignore[no-redef]
        """Stub crowd counting model (PyTorch not available)."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError(
                "CrowdCountingCNN requires PyTorch. "
                "Install with: pip install torch torchvision"
            )
