from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.processing_service import AIProcessingService
from app.db.models import Project, UploadJob
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


class UploadStorageError(Exception):
    """Raised when an uploaded file or its metadata cannot be stored."""


class ProjectNotFoundError(Exception):
    """Raised when an upload references a project that does not exist."""


def validate_image_file(file: UploadFile) -> None:
    """Require a recognized image extension and matching MIME type."""
    suffix = Path(file.filename or "").suffix.lower()
    expected_content_type = ALLOWED_IMAGE_TYPES.get(suffix)
    if not expected_content_type or file.content_type != expected_content_type:
        raise ValueError("Please upload a JPG, PNG, GIF, WEBP, or TIFF image file.")


def upload_job_response(job: UploadJob) -> dict:
    """Preserve the Phase 1 upload response contract."""
    return {
        "job_id": job.id,
        "project_name": job.project_name,
        "filename": job.original_filename,
        "size": job.file_size,
        "status": job.status,
        "timestamp": job.created_at.isoformat(),
        "reviewed_timestamp": job.reviewed_at.isoformat() if job.reviewed_at else None,
        "project_id": job.project_id,
    }


async def create_upload_job(
    db: Session,
    file: UploadFile,
    project_name: str,
    project_id: str | None = None,
) -> dict:
    """Store an image locally and persist its queued-job metadata."""
    job_id = str(uuid4())
    original_name = Path(file.filename or "upload").name
    suffix = Path(original_name).suffix.lower()
    stored_filename = f"{job_id}{suffix}"
    stored_path = UPLOAD_DIRECTORY / stored_filename
    project = db.get(Project, project_id) if project_id else None
    if project_id and not project:
        raise ProjectNotFoundError("Selected project was not found.")

    try:
        UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
        contents = await file.read()
        stored_path.write_bytes(contents)
    except OSError as error:
        raise UploadStorageError("Unable to store the uploaded file.") from error

    job = UploadJob(
        id=job_id,
        original_filename=original_name,
        stored_filename=stored_filename,
        file_size=len(contents),
        content_type=file.content_type,
        status="queued",
        project_name=project_name.strip(),
        project_id=project_id,
    )
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except SQLAlchemyError as error:
        db.rollback()
        raise UploadStorageError("Unable to save upload metadata.") from error

    try:
        job.status = "processing"
        db.commit()
        db.refresh(job)

        ai_service.queue(job_id, project_name)
        gis_service.prepare(job_id)

        job.status = "review"
        if project:
            project.status = "review"
        db.commit()
        db.refresh(job)

    except Exception as error:
        db.rollback()

        job.status = "error"
        db.commit()
        db.refresh(job)

        raise UploadStorageError(
            "AI/GIS processing failed."
        ) from error

    return upload_job_response(job)


def get_upload_job(db: Session, job_id: str) -> dict | None:
    """Return a persisted upload job record."""
    job = db.get(UploadJob, job_id)
    return upload_job_response(job) if job else None
