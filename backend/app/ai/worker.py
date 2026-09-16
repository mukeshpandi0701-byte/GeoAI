"""In-process worker foundation for queued imagery processing jobs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from app.ai.feature_handoff import ExtractedFeatureBatch, FeaturePersistencePort
from app.ai.image_preprocessing import preprocess_image
from app.ai.imagery_extraction import ExtractionError, LocalImageryExtractor
from app.db.database import SessionLocal
from app.db.models import UploadJob, utc_now
from app.gis.geometry import create_feature
from app.services.gis_features_service import GISFeaturePersistenceAdapter


class JobNotFoundError(RuntimeError):
    pass


class DuplicateProcessingError(RuntimeError):
    pass


class RetryNotAllowedError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProcessingResult:
    job_id: str
    status: str
    features: list[dict]
    failure_reason: str | None = None


class ProcessingWorker:
    """Claims one durable job at a time and runs local imagery extraction.

    There is intentionally no production queue dependency yet. A scheduler or
    queue consumer can call ``process_job`` / ``retry_job`` in a later phase.
    """

    def __init__(
        self,
        session_factory: sessionmaker = SessionLocal,
        feature_persistence: FeaturePersistencePort | None = None,
        extractor: LocalImageryExtractor | None = None,
        upload_directory: Path | None = None,
        max_processing_seconds: float = 30.0,
    ) -> None:
        self.session_factory = session_factory
        self.feature_persistence = feature_persistence or GISFeaturePersistenceAdapter(session_factory)
        self.extractor = extractor or LocalImageryExtractor()
        self.upload_directory = upload_directory or Path(__file__).resolve().parents[2] / "storage" / "uploads"
        if max_processing_seconds <= 0:
            raise ValueError("max_processing_seconds must be positive.")
        self.max_processing_seconds = max_processing_seconds

    def process_job(self, job_id: str) -> ProcessingResult:
        return self._process(job_id, allow_retry=False)

    def retry_job(self, job_id: str) -> ProcessingResult:
        return self._process(job_id, allow_retry=True)

    def _process(self, job_id: str, *, allow_retry: bool) -> ProcessingResult:
        worker_token = str(uuid4())
        with self.session_factory() as db:
            job = self._claim(db, job_id, worker_token, allow_retry)
            stored_path = self.upload_directory / job.stored_filename
            try:
                started = perf_counter()
                prepared = preprocess_image(stored_path)
                if not prepared.is_valid or prepared.image is None:
                    raise ExtractionError(prepared.error or "Unable to read imagery.")
                features = self.extractor.extract(prepared.image)
                features = self._validate_features(features)
                if perf_counter() - started > self.max_processing_seconds:
                    raise ExtractionError(
                        f"Processing timed out after {self.max_processing_seconds:g} seconds."
                    )
                self.feature_persistence.persist(
                    ExtractedFeatureBatch(job.id, job.project_id, features)
                )
            except (ExtractionError, OSError, ValueError) as error:
                return self._mark_failed(db, job, str(error))
            except Exception as error:  # Persistence/model errors are visible and retryable.
                return self._mark_failed(db, job, f"Processing failed: {error}")

            job.status = "review"
            job.processing_completed_at = utc_now()
            job.failure_reason = None
            job.failed_at = None
            job.worker_token = None
            if job.project:
                job.project.status = "review"
            db.commit()
            return ProcessingResult(job.id, job.status, features)

    def _claim(self, db: Session, job_id: str, worker_token: str, allow_retry: bool) -> UploadJob:
        job = db.get(UploadJob, job_id)
        if not job:
            raise JobNotFoundError("Processing job was not found.")
        if job.status == "failed" and not allow_retry:
            raise RetryNotAllowedError("Failed jobs must be retried explicitly.")
        expected_status = "failed" if allow_retry else "queued"
        if job.status != expected_status:
            raise DuplicateProcessingError(f"Job cannot be claimed while its status is {job.status}.")

        started_at = utc_now()
        values = {
            "status": "processing",
            "processing_started_at": started_at,
            "processing_completed_at": None,
            "failed_at": None,
            "failure_reason": None,
            "worker_token": worker_token,
        }
        if allow_retry:
            values["retry_count"] = UploadJob.retry_count + 1
        claimed = db.execute(
            update(UploadJob)
            .where(UploadJob.id == job_id, UploadJob.status == expected_status)
            .values(**values)
        )
        if claimed.rowcount != 1:
            db.rollback()
            raise DuplicateProcessingError("Job was claimed by another worker.")
        db.commit()
        return db.get(UploadJob, job_id)

    @staticmethod
    def _mark_failed(db: Session, job: UploadJob, reason: str) -> ProcessingResult:
        job.status = "failed"
        job.failed_at = utc_now()
        job.failure_reason = reason
        job.worker_token = None
        db.commit()
        return ProcessingResult(job.id, job.status, [], reason)

    @staticmethod
    def _validate_features(features: list[dict]) -> list[dict]:
        """Revalidate model output before it is handed to GIS persistence."""
        validated: list[dict] = []
        for feature in features:
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                raise ExtractionError("Extraction failed: generated feature is not a GeoJSON Feature.")
            properties = feature.get("properties")
            feature_type = properties.get("feature_type") if isinstance(properties, dict) else None
            try:
                validated.append(create_feature(feature_type, feature.get("geometry"), properties))
            except (TypeError, ValueError) as error:
                raise ExtractionError(f"Extraction failed: invalid generated geometry: {error}") from error
        if not validated:
            raise ExtractionError("Extraction failed: no features were generated.")
        return validated
