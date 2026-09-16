"""Deterministic, local image-to-feature extraction heuristics.

This is a lightweight computer-vision baseline, not a trained cadastral model.
It segments high-contrast imagery into physical building and road candidates and
derives *indicative* parcel envelopes.  Coordinates are normalized image-space
coordinates, so downstream GIS work must georeference them before map display.
"""

from __future__ import annotations

from dataclasses import dataclass
from PIL import Image, ImageOps

from app.gis.geometry import create_feature


class ExtractionError(RuntimeError):
    """Raised when imagery cannot produce a trustworthy extraction."""


@dataclass(frozen=True)
class Component:
    left: int
    top: int
    right: int
    bottom: int
    pixels: int

    @property
    def width(self) -> int:
        return self.right - self.left + 1

    @property
    def height(self) -> int:
        return self.bottom - self.top + 1


class LocalImageryExtractor:
    """Extract simple physical feature candidates without external AI services."""

    minimum_dimension = 32
    minimum_contrast = 8.0
    dark_pixel_threshold = 170
    minimum_component_pixels = 20

    def extract(self, image: Image.Image) -> list[dict]:
        if min(image.size) < self.minimum_dimension:
            raise ExtractionError("Image quality is insufficient: image must be at least 32 pixels on each side.")

        grayscale = ImageOps.grayscale(image)
        values = list(grayscale.tobytes())
        if not values or max(values) - min(values) < self.minimum_contrast:
            raise ExtractionError("Image quality is insufficient: image contrast is too low for feature extraction.")

        components = self._dark_components(grayscale)
        if not components:
            raise ExtractionError("Extraction failed: no physical feature candidates were found in the imagery.")

        features: list[dict] = []
        building_components: list[Component] = []
        road_components: list[Component] = []
        for component in components:
            aspect_ratio = max(component.width, component.height) / min(component.width, component.height)
            if aspect_ratio >= 3 and max(component.width, component.height) >= 24:
                road_components.append(component)
                features.append(self._road_feature(component, image.size))
            else:
                building_components.append(component)
                features.append(self._building_feature(component, image.size))

        # Indicative parcels are image-derived envelopes, never legal or cadastral
        # boundaries. They give reviewers a physical-area candidate to inspect.
        for component in building_components or road_components[:1]:
            features.append(self._indicative_parcel_feature(component, image.size))

        return features

    def _dark_components(self, image: Image.Image) -> list[Component]:
        width, height = image.size
        pixels = list(image.tobytes())
        mask = [value <= self.dark_pixel_threshold for value in pixels]
        visited = bytearray(width * height)
        components: list[Component] = []

        for start, is_dark in enumerate(mask):
            if not is_dark or visited[start]:
                continue
            stack = [start]
            visited[start] = 1
            left = right = start % width
            top = bottom = start // width
            count = 0
            while stack:
                index = stack.pop()
                x, y = index % width, index // width
                count += 1
                left, right = min(left, x), max(right, x)
                top, bottom = min(top, y), max(bottom, y)
                for neighbour_x, neighbour_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= neighbour_x < width and 0 <= neighbour_y < height:
                        neighbour = neighbour_y * width + neighbour_x
                        if mask[neighbour] and not visited[neighbour]:
                            visited[neighbour] = 1
                            stack.append(neighbour)
            if count >= self.minimum_component_pixels:
                components.append(Component(left, top, right, bottom, count))
        return components

    @staticmethod
    def _point(x: int, y: int, size: tuple[int, int]) -> list[float]:
        width, height = size
        return [round(x / max(width - 1, 1), 6), round(y / max(height - 1, 1), 6)]

    def _polygon(self, component: Component, size: tuple[int, int], padding: int = 0) -> dict:
        width, height = size
        left = max(component.left - padding, 0)
        top = max(component.top - padding, 0)
        right = min(component.right + padding, width - 1)
        bottom = min(component.bottom + padding, height - 1)
        return {
            "type": "Polygon",
            "coordinates": [[
                self._point(left, top, size),
                self._point(right, top, size),
                self._point(right, bottom, size),
                self._point(left, bottom, size),
                self._point(left, top, size),
            ]],
        }

    def _confidence(self, component: Component) -> float:
        density = component.pixels / (component.width * component.height)
        return round(min(0.99, max(0.3, 0.45 + density * 0.5)), 3)

    def _building_feature(self, component: Component, size: tuple[int, int]) -> dict:
        return create_feature(
            "building",
            self._polygon(component, size),
            {
                "confidence": self._confidence(component),
                "source": "local-image-segmentation",
                "coordinate_reference": "normalized-image-space",
            },
        )

    def _road_feature(self, component: Component, size: tuple[int, int]) -> dict:
        if component.width >= component.height:
            coordinates = [
                self._point(component.left, (component.top + component.bottom) // 2, size),
                self._point(component.right, (component.top + component.bottom) // 2, size),
            ]
        else:
            coordinates = [
                self._point((component.left + component.right) // 2, component.top, size),
                self._point((component.left + component.right) // 2, component.bottom, size),
            ]
        return create_feature(
            "road",
            {"type": "LineString", "coordinates": coordinates},
            {
                "confidence": self._confidence(component),
                "source": "local-image-segmentation",
                "coordinate_reference": "normalized-image-space",
            },
        )

    def _indicative_parcel_feature(self, component: Component, size: tuple[int, int]) -> dict:
        return create_feature(
            "parcel",
            self._polygon(component, size, padding=4),
            {
                "confidence": self._confidence(component),
                "source": "local-image-segmentation",
                "coordinate_reference": "normalized-image-space",
                "boundary_classification": "indicative_physical_boundary",
                "legal_status": "not_a_legal_or_cadastral_boundary",
            },
        )
