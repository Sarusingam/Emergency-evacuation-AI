"""
Preprocessing — Resize, normalize, augment, generate density maps.

Common preprocessing utilities shared by all dataset loaders.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def resize_image(
    image: np.ndarray,
    target_size: tuple[int, int] = (640, 640),
) -> np.ndarray:
    """Resize image to target size.

    Args:
        image: Input image (H×W×C).
        target_size: (height, width) target.

    Returns:
        Resized image.
    """
    try:
        import cv2
        return cv2.resize(image, (target_size[1], target_size[0]))
    except ImportError:
        # Crude fallback without OpenCV
        from PIL import Image
        pil_img = Image.fromarray(image)
        pil_img = pil_img.resize((target_size[1], target_size[0]))
        return np.array(pil_img)


def normalize_image(
    image: np.ndarray,
    mean: tuple[float, ...] = (0.485, 0.456, 0.406),
    std: tuple[float, ...] = (0.229, 0.224, 0.225),
) -> np.ndarray:
    """Normalize image with ImageNet mean and std.

    Args:
        image: Input image (H×W×C), uint8 or float.
        mean: Channel means.
        std: Channel standard deviations.

    Returns:
        Normalized float32 image.
    """
    img = image.astype(np.float32) / 255.0
    img = (img - np.array(mean)) / np.array(std)
    return img.astype(np.float32)


def generate_density_map(
    image_shape: tuple[int, int],
    points: list[tuple[float, float]],
    sigma: float = 15.0,
) -> np.ndarray:
    """Generate a Gaussian density map from point annotations.

    Each annotated point is convolved with a Gaussian kernel
    to produce a continuous density map.

    Args:
        image_shape: (height, width) of the target density map.
        points: List of (x, y) annotation points.
        sigma: Gaussian kernel standard deviation.

    Returns:
        Density map as float32 numpy array (H×W).
    """
    h, w = image_shape
    density = np.zeros((h, w), dtype=np.float32)

    if not points:
        return density

    for x, y in points:
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < w and 0 <= yi < h:
            # Simple Gaussian around the point
            y_grid, x_grid = np.ogrid[
                max(0, yi - 3 * int(sigma)):min(h, yi + 3 * int(sigma) + 1),
                max(0, xi - 3 * int(sigma)):min(w, xi + 3 * int(sigma) + 1),
            ]
            gaussian = np.exp(
                -((x_grid - xi) ** 2 + (y_grid - yi) ** 2)
                / (2 * sigma ** 2)
            )
            density[
                max(0, yi - 3 * int(sigma)):min(h, yi + 3 * int(sigma) + 1),
                max(0, xi - 3 * int(sigma)):min(w, xi + 3 * int(sigma) + 1),
            ] += gaussian

    return density


def random_crop(
    image: np.ndarray,
    density_map: np.ndarray | None = None,
    crop_size: tuple[int, int] = (256, 256),
) -> tuple[np.ndarray, np.ndarray | None]:
    """Random crop for data augmentation.

    Args:
        image: Input image.
        density_map: Optional density map to crop in sync.
        crop_size: (height, width) of the crop.

    Returns:
        Tuple of (cropped_image, cropped_density_map_or_None).
    """
    h, w = image.shape[:2]
    ch, cw = crop_size

    if h <= ch or w <= cw:
        return image, density_map

    y = np.random.randint(0, h - ch)
    x = np.random.randint(0, w - cw)

    cropped = image[y:y + ch, x:x + cw]
    cropped_density = None
    if density_map is not None:
        cropped_density = density_map[y:y + ch, x:x + cw]

    return cropped, cropped_density


def horizontal_flip(
    image: np.ndarray,
    density_map: np.ndarray | None = None,
    probability: float = 0.5,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Random horizontal flip.

    Args:
        image: Input image.
        density_map: Optional density map.
        probability: Flip probability.

    Returns:
        Tuple of (image, density_map), possibly flipped.
    """
    if np.random.random() < probability:
        image = np.fliplr(image).copy()
        if density_map is not None:
            density_map = np.fliplr(density_map).copy()
    return image, density_map
