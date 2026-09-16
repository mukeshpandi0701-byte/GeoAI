from fastapi.testclient import TestClient

from app.db.database import SessionLocal, init_db
from app.db.models import GISFeature, Project, UploadJob
from app.main import app

client = TestClient(app)

POLYGON = {"type": "Polygon", "coordinates": [[[77.0, 12.0], [77.01, 12.0], [77.01, 12.01], [77.0, 12.0]]]}
LINE = {"type": "LineString", "coordinates": [[77.0, 12.0], [77.02, 12.02]]}


def setup_function():
    init_db()
    with SessionLocal() as db:
        db.query(GISFeature).delete()
        db.query(UploadJob).delete()
        db.query(Project).delete()
        db.commit()


def project():
    return client.post("/api/projects", json={"name": "Feature Survey"}).json()


def payload(project_id, **overrides):
    base = {"project_id": project_id, "feature_type": "building", "geometry": POLYGON, "properties": {"source": "drone-ai"}}
    base.update(overrides)
    return base


def test_creates_and_retrieves_geojson_feature():
    created = client.post("/api/features", json=payload(project()["project_id"]))
    assert created.status_code == 201
    feature = created.json()
    assert feature["type"] == "Feature"
    assert feature["properties"] == {"feature_type": "building", "source": "drone-ai"}
    assert feature["review_status"] == "pending"
    assert client.get(f"/api/features/{feature['id']}").json()["id"] == feature["id"]


def test_feature_associates_with_upload_job_and_filters():
    current_project = project()
    with SessionLocal() as db:
        job = UploadJob(original_filename="image.png", stored_filename="image.png", file_size=1, content_type="image/png", project_name="Feature Survey", project_id=current_project["project_id"])
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id
    created = client.post("/api/features", json=payload(current_project["project_id"], upload_job_id=job_id, feature_type="road", geometry=LINE))
    assert created.status_code == 201
    assert client.get(f"/api/features?project_id={current_project['project_id']}&upload_job_id={job_id}&feature_type=road").json()[0]["id"] == created.json()["id"]


def test_updates_geometry_and_review_decision():
    created = client.post("/api/features", json=payload(project()["project_id"])).json()
    updated_polygon = {"type": "Polygon", "coordinates": [[[77.1, 12.1], [77.11, 12.1], [77.11, 12.11], [77.1, 12.1]]]}
    response = client.patch(f"/api/features/{created['id']}", json={"geometry": updated_polygon, "feature_type": "building", "review_status": "accepted", "reviewer": "map reviewer", "reviewer_note": "Visible rooftop confirmed."})
    assert response.status_code == 200
    assert response.json()["geometry"] == updated_polygon
    assert response.json()["review_status"] == "accepted"
    assert response.json()["reviewer_note"] == "Visible rooftop confirmed."
    assert response.json()["reviewed_at"]


def test_rejects_and_filters_feature():
    created = client.post("/api/features", json=payload(project()["project_id"])).json()
    client.patch(f"/api/features/{created['id']}", json={"review_status": "rejected", "reviewer_note": "Image obscured."})
    rejected = client.get("/api/features?review_status=rejected").json()
    assert rejected[0]["id"] == created["id"]
    assert rejected[0]["review_status"] == "rejected"


def test_deletes_feature():
    created = client.post("/api/features", json=payload(project()["project_id"])).json()
    assert client.delete(f"/api/features/{created['id']}").status_code == 204
    assert client.get(f"/api/features/{created['id']}").status_code == 404


def test_rejects_invalid_feature_type_and_geometry():
    project_id = project()["project_id"]
    invalid_type = client.post("/api/features", json=payload(project_id, feature_type="tree"))
    invalid_geometry = client.post("/api/features", json=payload(project_id, geometry={"type": "Polygon", "coordinates": [[[77, 12], [78, 12], [78, 13]]]}))
    assert invalid_type.status_code == 422
    assert invalid_type.json()["detail"] == "Feature type must be building, road, or parcel."
    assert invalid_geometry.json()["detail"] == "Polygon linear rings must contain at least four positions."


def test_rejects_self_intersection_and_duplicate_geometry():
    project_id = project()["project_id"]
    bow_tie = {"type": "Polygon", "coordinates": [[[77, 12], [78, 13], [78, 12], [77, 13], [77, 12]]]}
    assert client.post("/api/features", json=payload(project_id, geometry=bow_tie)).json()["detail"] == "Polygon ring must not self-intersect."
    assert client.post("/api/features", json=payload(project_id)).status_code == 201
    duplicate = client.post("/api/features", json=payload(project_id))
    assert duplicate.status_code == 422
    assert duplicate.json()["detail"] == "Duplicate feature geometry already exists in this project."


def test_road_parcel_overlap_is_warning_not_cadastral_claim():
    project_id = project()["project_id"]
    client.post("/api/features", json=payload(project_id, feature_type="parcel"))
    road = client.post("/api/features", json=payload(project_id, feature_type="road", geometry=LINE)).json()
    assert road["validation_warnings"] == ["Road and parcel bounding boxes overlap; review the mapped feature geometry."]
