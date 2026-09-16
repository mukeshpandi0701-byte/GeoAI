"""Small GeoJSON-compatible geometry helpers for physical feature mapping.

This module describes mapped physical features only. It does not establish land
ownership, legal parcel boundaries, or cadastral validity.
"""

from copy import deepcopy
from math import isfinite
from typing import Any


FEATURE_GEOMETRY_TYPES = {
    "building": "Polygon",
    "parcel": "Polygon",
    "road": "LineString",
}
SUPPORTED_GEOMETRY_TYPES = {"Point", "LineString", "Polygon"}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def _validate_position(position: Any) -> None:
    if not isinstance(position, list) or len(position) != 2:
        raise ValueError("Coordinate positions must contain exactly two numeric values.")
    if not all(_is_number(value) for value in position):
        raise ValueError("Coordinate positions must contain exactly two numeric values.")


def _validate_line_string(coordinates: Any) -> None:
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("Geometry coordinates must not be empty.")
    if len(coordinates) < 2:
        raise ValueError("LineString geometry must contain at least two positions.")
    for position in coordinates:
        _validate_position(position)


def _validate_polygon(coordinates: Any) -> None:
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("Geometry coordinates must not be empty.")
    for ring in coordinates:
        if not isinstance(ring, list) or not ring:
            raise ValueError("Polygon geometry must contain at least one linear ring.")
        if len(ring) < 4:
            raise ValueError("Polygon linear rings must contain at least four positions.")
        for position in ring:
            _validate_position(position)
        if ring[0] != ring[-1]:
            raise ValueError("Polygon linear rings must be closed.")


def validate_geometry(geometry: Any) -> None:
    """Validate a small, predictable subset of GeoJSON geometry objects.

    Coordinates use GeoJSON order: ``[longitude, latitude]``. The function
    raises ``ValueError`` with stable messages when the input is invalid.
    """
    if not isinstance(geometry, dict):
        raise ValueError("Geometry must be an object.")

    geometry_type = geometry.get("type")
    if geometry_type not in SUPPORTED_GEOMETRY_TYPES:
        raise ValueError("Geometry type must be Point, LineString, or Polygon.")

    if "coordinates" not in geometry:
        raise ValueError("Geometry must include coordinates.")

    coordinates = geometry["coordinates"]
    if geometry_type == "Point":
        _validate_position(coordinates)
    elif geometry_type == "LineString":
        _validate_line_string(coordinates)
    else:
        _validate_polygon(coordinates)


def create_feature(
    feature_type: str,
    geometry: dict[str, Any],
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a validated GeoJSON-like Feature for a mapped physical feature."""
    expected_geometry_type = FEATURE_GEOMETRY_TYPES.get(feature_type)
    if not expected_geometry_type:
        raise ValueError("Feature type must be building, road, or parcel.")

    validate_geometry(geometry)
    if geometry["type"] != expected_geometry_type:
        raise ValueError(
            f"{feature_type.capitalize()} features must use {expected_geometry_type} geometry."
        )
    if properties is not None and not isinstance(properties, dict):
        raise ValueError("Feature properties must be an object.")

    feature_properties = deepcopy(properties) if properties else {}
    feature_properties["feature_type"] = feature_type
    return {
        "type": "Feature",
        "geometry": deepcopy(geometry),
        "properties": feature_properties,
    }
