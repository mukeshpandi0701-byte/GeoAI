from fastapi.testclient import TestClient

from app.db.database import SessionLocal, engine, init_db
from app.db.models import GISFeature, Project, UploadJob
from app.main import app


client = TestClient(app)


def setup_function():
    init_db()
    with SessionLocal() as db:
        db.query(GISFeature).delete()
        db.query(UploadJob).delete()
        db.query(Project).delete()
        db.commit()


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "configured"}


def test_valid_image_upload_creates_queued_job():
    response = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Central Ward Survey"},
        files={"file": ("parcel.png", b"mock image data", "image/png")},
    )

    assert response.status_code == 202
    job = response.json()
    assert job["filename"] == "parcel.png"
    assert job["size"] == len(b"mock image data")
    assert job["status"] == "queued"
    assert job["timestamp"]


def test_invalid_file_is_rejected():
    response = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Central Ward Survey"},
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415


def test_upload_endpoint_accepts_frontend_multipart_form_data():
    response = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Frontend integration"},
        files={"file": ("parcel.webp", b"mock webp data", "image/webp")},
    )

    assert response.status_code == 202
    assert response.json()["project_name"] == "Frontend integration"


def test_upload_metadata_is_persisted():
    created = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Central Ward Survey"},
        files={"file": ("parcel.jpg", b"stored metadata", "image/jpeg")},
    ).json()

    with SessionLocal() as db:
        job = db.get(UploadJob, created["job_id"])
        assert job is not None
        assert job.original_filename == "parcel.jpg"
        assert job.stored_filename.endswith(".jpg")
        assert job.file_size == len(b"stored metadata")
        assert job.content_type == "image/jpeg"


def test_job_status_lookup():
    created = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Central Ward Survey"},
        files={"file": ("parcel.jpg", b"mock jpg data", "image/jpeg")},
    ).json()

    response = client.get(f"/api/uploads/{created['job_id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_reviewed_upload_remains_available_after_approval():
    created = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Central Ward Survey"},
        files={"file": ("parcel.jpg", b"mock jpg data", "image/jpeg")},
    ).json()

    assert created["status"] == "queued"
    with SessionLocal() as db:
        job = db.get(UploadJob, created["job_id"])
        job.status = "review"
        db.commit()
    response = client.patch(
        f"/api/review-queue/{created['job_id']}?decision=approved"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert client.get("/api/review-queue").json() == []
    assert client.get("/api/review-queue?status=approved").json()[0]["job_id"] == created["job_id"]


def test_upload_can_be_linked_to_project_and_appears_in_history():
    project = client.post("/api/projects", json={"name": "Central Ward"}).json()

    created = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Central Ward", "project_id": project["project_id"]},
        files={"file": ("parcel.png", b"linked upload", "image/png")},
    ).json()

    assert created["project_id"] == project["project_id"]
    detail = client.get(f"/api/projects/{project['project_id']}").json()
    assert detail["status"] == "created"
    assert detail["upload_summary"]["queued"] == 1
    history = client.get(f"/api/projects/{project['project_id']}/uploads").json()
    assert history[0] == created | {"feature_count": 0}


def test_project_history_includes_processing_metadata_and_feature_count():
    project = client.post("/api/projects", json={"name": "History project"}).json()
    job = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "History project", "project_id": project["project_id"]},
        files={"file": ("history.png", b"image", "image/png")},
    ).json()
    with SessionLocal() as db:
        stored_job = db.get(UploadJob, job["job_id"])
        stored_job.status = "failed"
        stored_job.failure_reason = "Image could not be read."
        stored_job.retry_count = 2
        db.commit()

    history = client.get(f"/api/projects/{project['project_id']}/uploads")

    assert history.status_code == 200
    item = history.json()[0]
    assert item["status"] == "failed"
    assert item["failure_reason"] == "Image could not be read."
    assert item["retry_count"] == 2
    assert item["feature_count"] == 0


def test_empty_project_history_and_invalid_project():
    project = client.post("/api/projects", json={"name": "Empty history"}).json()

    assert client.get(f"/api/projects/{project['project_id']}/uploads").json() == []
    assert client.get("/api/projects/not-a-project/uploads").status_code == 404


def test_project_history_counts_persisted_features_for_its_upload():
    project = client.post("/api/projects", json={"name": "Feature history"}).json()
    job = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Feature history", "project_id": project["project_id"]},
        files={"file": ("feature.png", b"image", "image/png")},
    ).json()
    feature = client.post("/api/features", json={
        "project_id": project["project_id"], "upload_job_id": job["job_id"], "feature_type": "building",
        "geometry": {"type": "Polygon", "coordinates": [[[77, 12], [77.01, 12], [77.01, 12.01], [77, 12]]]},
        "properties": {"source": "drone-ai"},
    })

    assert feature.status_code == 201
    assert client.get(f"/api/projects/{project['project_id']}/uploads").json()[0]["feature_count"] == 1


def test_retry_endpoint_rejects_jobs_that_have_not_failed():
    job = client.post(
        "/api/uploads/drone-image", data={"project_name": "Retry"},
        files={"file": ("retry.png", b"image", "image/png")},
    ).json()

    assert client.post(f"/api/uploads/{job['job_id']}/retry").status_code == 409


def test_retry_endpoint_uses_existing_worker_and_increments_retry_count():
    job = client.post(
        "/api/uploads/drone-image", data={"project_name": "Retry"},
        files={"file": ("retry.png", b"not a valid image", "image/png")},
    ).json()
    with SessionLocal() as db:
        db.get(UploadJob, job["job_id"]).status = "failed"
        db.commit()

    retried = client.post(f"/api/uploads/{job['job_id']}/retry")

    assert retried.status_code == 200
    assert retried.json()["status"] == "failed"
    assert retried.json()["retry_count"] == 1


def test_approval_records_timestamp_and_publishes_linked_project():
    project = client.post("/api/projects", json={"name": "Central Ward"}).json()
    job = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Central Ward", "project_id": project["project_id"]},
        files={"file": ("parcel.png", b"linked upload", "image/png")},
    ).json()
    with SessionLocal() as db:
        stored_job = db.get(UploadJob, job["job_id"])
        stored_job.status = "review"
        db.commit()

    approved = client.patch(
        f"/api/review-queue/{job['job_id']}?decision=approved"
    ).json()

    assert approved["status"] == "approved"
    assert approved["reviewed_timestamp"]
    detail = client.get(f"/api/projects/{project['project_id']}").json()
    assert detail["status"] == "published"
    assert detail["upload_summary"]["approved"] == 1


def test_upload_with_unknown_project_is_rejected():
    response = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Missing", "project_id": "not-a-project"},
        files={"file": ("parcel.png", b"mock image data", "image/png")},
    )

    assert response.status_code == 404


def test_project_creation():
    response = client.post(
        "/api/projects",
        json={"name": "Central Ward", "description": "Survey area", "location": "Ward 4"},
    )

    assert response.status_code == 201
    project = response.json()
    assert project["project_name"] == "Central Ward"
    assert project["status"] == "created"
    assert project["created_timestamp"]


def test_project_listing():
    client.post("/api/projects", json={"name": "First"})
    client.post("/api/projects", json={"name": "Second"})

    response = client.get("/api/projects")

    assert response.status_code == 200
    assert [project["project_name"] for project in response.json()] == ["Second", "First"]


def test_project_lookup():
    created = client.post("/api/projects", json={"name": "Central Ward"}).json()

    response = client.get(f"/api/projects/{created['project_id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_invalid_project_id_returns_not_found():
    response = client.get("/api/projects/not-a-real-project")

    assert response.status_code == 404


def test_project_survives_database_reconnect():
    created = client.post("/api/projects", json={"name": "Persistent project"}).json()

    engine.dispose()
    init_db()
    response = client.get(f"/api/projects/{created['project_id']}")

    assert response.status_code == 200
    assert response.json()["project_name"] == "Persistent project"
