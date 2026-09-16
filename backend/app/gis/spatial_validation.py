"""Lightweight warnings for mapped features; not cadastral or legal validation."""

from collections.abc import Mapping
from typing import Any


def _positions(geometry: Mapping[str, Any]) -> list[list[float]]:
    coordinates = geometry["coordinates"]
    if geometry["type"] == "Point":
        return [coordinates]
    if geometry["type"] == "LineString":
        return coordinates
    return coordinates[0]


def bounding_box(geometry: Mapping[str, Any]) -> tuple[float, float, float, float]:
    positions = _positions(geometry)
    longitudes, latitudes = zip(*positions)
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def boxes_overlap(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    first_box, second_box = bounding_box(first), bounding_box(second)
    return not (first_box[2] < second_box[0] or second_box[2] < first_box[0] or first_box[3] < second_box[1] or second_box[3] < first_box[1])


def overlap_warnings(feature_type: str, geometry: Mapping[str, Any], existing: list[tuple[str, Mapping[str, Any]]]) -> list[str]:
    warnings: list[str] = []
    for other_type, other_geometry in existing:
        if {feature_type, other_type} == {"road", "parcel"} and boxes_overlap(geometry, other_geometry):
            warnings.append("Road and parcel bounding boxes overlap; review the mapped feature geometry.")
            break
    return warnings


def ensure_no_polygon_self_intersection(geometry: Mapping[str, Any]) -> None:
    """Reject a self-crossing polygon ring before it is stored."""
    if geometry["type"] != "Polygon":
        return
    ring = [tuple(position) for position in geometry["coordinates"][0]]
    edges = len(ring) - 1

    def orientation(first, second, third):
        value = (second[1] - first[1]) * (third[0] - second[0]) - (second[0] - first[0]) * (third[1] - second[1])
        return 0 if value == 0 else (1 if value > 0 else 2)

    for first in range(edges):
        for second in range(first + 1, edges):
            if second in {first, first + 1} or (first == 0 and second == edges - 1):
                continue
            a, b, c, d = ring[first], ring[first + 1], ring[second], ring[second + 1]
            if orientation(a, b, c) != orientation(a, b, d) and orientation(c, d, a) != orientation(c, d, b):
                raise ValueError("Polygon ring must not self-intersect.")
