import pytest

from app.gis.geometry import create_feature, validate_geometry


def test_creates_a_building_feature_with_geojson_structure():
    geometry = {
        "type": "Polygon",
        "coordinates": [[[77.59, 12.97], [77.60, 12.97], [77.60, 12.98], [77.59, 12.97]]],
    }

    feature = create_feature("building", geometry, {"source": "drone"})

    assert feature == {
        "type": "Feature",
        "geometry": geometry,
        "properties": {"source": "drone", "feature_type": "building"},
    }


def test_creates_a_road_feature():
    feature = create_feature(
        "road",
        {"type": "LineString", "coordinates": [[77.59, 12.97], [77.60, 12.98]]},
    )

    assert feature["properties"]["feature_type"] == "road"


def test_validates_a_point_geometry():
    validate_geometry({"type": "Point", "coordinates": [77.59, 12.97]})


@pytest.mark.parametrize(
    ("geometry", "message"),
    [
        ({"type": "LineString", "coordinates": []}, "Geometry coordinates must not be empty."),
        ({"type": "Polygon", "coordinates": [[[77.59, 12.97], [77.60, 12.97], [77.60, 12.98]]]}, "Polygon linear rings must contain at least four positions."),
        ({"type": "Polygon", "coordinates": [[[77.59, 12.97], [77.60, 12.97], [77.60, 12.98], [77.59, 12.98]]]}, "Polygon linear rings must be closed."),
        ({"type": "Point", "coordinates": ["77.59", 12.97]}, "Coordinate positions must contain exactly two numeric values."),
    ],
)
def test_rejects_invalid_or_empty_geometries(geometry, message):
    with pytest.raises(ValueError, match=message):
        validate_geometry(geometry)


def test_rejects_feature_with_an_incompatible_geometry_type():
    with pytest.raises(ValueError, match="Road features must use LineString geometry."):
        create_feature("road", {"type": "Point", "coordinates": [77.59, 12.97]})
