"""Small, model-agnostic image preparation utilities for parcel extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps, UnidentifiedImageError


@dataclass(frozen=True)
class ImageProperties:
    """Basic properties observed before the image is prepared."""

    source_format: str
    original_mode: str
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int


@dataclass(frozen=True)
class PreprocessingResult:
    """The stable outcome of attempting to prepare one input image."""

    image: Image.Image | None
    properties: ImageProperties | None
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.image is not None and self.properties is not None


def preprocess_image(
    source: str | Path | BinaryIO,
    *,
    max_dimension: int | None = 2048,
) -> PreprocessingResult:
    """Load an image, normalize it to RGB, and downsize it when needed.

    Invalid or unreadable input is reported as a failed result rather than an
    exception so callers can safely route it to a rejected-upload state.
    """
    if max_dimension is not None and max_dimension <= 0:
        return PreprocessingResult(
            image=None,
            properties=None,
            error="max_dimension must be a positive integer or None.",
        )

    try:
        with Image.open(source) as opened_image:
            opened_image.load()
            source_format = opened_image.format or "unknown"
            original_mode = opened_image.mode
            original_width, original_height = opened_image.size

            # Respect camera orientation and detach pixel data from the source.
            processed_image = ImageOps.exif_transpose(opened_image).convert("RGB")
    except (Image.DecompressionBombError, OSError, UnidentifiedImageError, ValueError, TypeError) as error:
        return PreprocessingResult(
            image=None,
            properties=None,
            error=f"Unable to read image: {error}",
        )

    if max_dimension is not None and max(processed_image.size) > max_dimension:
        processed_image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    processed_width, processed_height = processed_image.size
    return PreprocessingResult(
        image=processed_image,
        properties=ImageProperties(
            source_format=source_format,
            original_mode=original_mode,
            original_width=original_width,
            original_height=original_height,
            processed_width=processed_width,
            processed_height=processed_height,
        ),
    )
