from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.ai.processing_service import AIProcessingService
from app.gis.processing_service import GISProcessingService

ai_service = AIProcessingService()
gis_service = GISProcessingService()

UPLOAD_DIRECTORY = Path(__file__).resolve().parents[2] / "storage" / "uploads"
ALLOWED_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}
upload_jobs: dict[str, dict] = {}


class UploadStorageError(Exception):
    """Raised when an uploaded file cannot be stored locally."""


def validate_image_file(file: UploadFile) -> None:
    """Require a recognized image extension and matching MIME type."""
    suffix = Path(file.filename or "").suffix.lower()
    expected_content_type = ALLOWED_IMAGE_TYPES.get(suffix)
    if not expected_content_type or file.content_type != expected_content_type:
        raise ValueError("Please upload a JPG, PNG, GIF, WEBP, or TIFF image file.")

async def create_upload_job(file: UploadFile, project_name: str) -> dict:
    """Store an upload locally and create an in-memory mock processing job."""
    job_id = str(uuid4())
    original_name = Path(file.filename or "upload").name
    suffix = Path(original_name).suffix.lower()
    stored_path = UPLOAD_DIRECTORY / f"{job_id}{suffix}"

    try:
        UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
        contents = await file.read()
        stored_path.write_bytes(contents)
    except OSError as error:
        raise UploadStorageError("Unable to store the uploaded file.") from error

    timestamp = datetime.now(timezone.utc).isoformat()
    job = {
        "job_id": job_id,
        "project_name": project_name.strip(),
        "filename": original_name,
        "size": len(contents),
        "status": "queued",
        "timestamp": timestamp,
    }
    upload_jobs[job_id] = job
    ai_service.queue(job_id, project_name)
    gis_service.prepare(job_id)
    return job


def get_upload_job(job_id: str) -> dict | None:
    """Return a mock job record while the current server process is running."""
    return upload_jobs.get(job_id)
