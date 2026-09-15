from fastapi.testclient import TestClient

from app.main import app
from app.services.project_service import upload_jobs

client = TestClient(app)


def setup_function():
    upload_jobs.clear()


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "not configured"}


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


def test_job_status_lookup():
    created = client.post(
        "/api/uploads/drone-image",
        data={"project_name": "Central Ward Survey"},
        files={"file": ("parcel.jpg", b"mock jpg data", "image/jpeg")},
    ).json()

    response = client.get(f"/api/uploads/{created['job_id']}")

    assert response.status_code == 200
    assert response.json() == created
