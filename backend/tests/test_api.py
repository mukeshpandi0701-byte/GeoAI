from fastapi.testclient import TestClient

from app.db.database import SessionLocal, engine, init_db
from app.db.models import Project, UploadJob
from app.main import app


client = TestClient(app)


def setup_function():
    init_db()
    with SessionLocal() as db:
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
