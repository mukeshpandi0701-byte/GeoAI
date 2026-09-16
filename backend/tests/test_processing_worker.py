from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from app.ai.feature_handoff import ExtractedFeatureBatch
from app.ai.worker import DuplicateProcessingError, ProcessingWorker
from app.db.database import SessionLocal, init_db
from app.db.models import GISFeature, Project, UploadJob


def sample_imagery() -> bytes:
    image = Image.new("RGB", (100, 100), "white")
    drawing = ImageDraw.Draw(image)
    drawing.rectangle((20, 20, 50, 50), fill="black")
    drawing.rectangle((0, 72, 99, 82), fill="black")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class RecordingPersistence:
    def __init__(self) -> None:
        self.batches: list[ExtractedFeatureBatch] = []

    def persist(self, batch: ExtractedFeatureBatch) -> None:
        self.batches.append(batch)


class FailingPersistence:
    def persist(self, batch: ExtractedFeatureBatch) -> None:
        raise RuntimeError("GIS feature persistence unavailable")


class InvalidGeometryExtractor:
    def extract(self, image: Image.Image) -> list[dict]:
        return [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"feature_type": "road"},
        }]


@pytest.fixture(autouse=True)
def clean_database():
    init_db()
    with SessionLocal() as db:
        db.query(GISFeature).delete()
        db.query(UploadJob).delete()
        db.query(Project).delete()
        db.commit()


@pytest.fixture
def uploads_path() -> Path:
    path = Path(__file__).resolve().parents[1] / "storage" / "worker_test_uploads"
    path.mkdir(parents=True, exist_ok=True)
    for file_path in path.iterdir():
        file_path.unlink()
    return path


def create_job(uploads_path: Path, *, image_data: bytes | None = None) -> UploadJob:
    stored_filename = "imagery.png"
    if image_data is not None:
        (uploads_path / stored_filename).write_bytes(image_data)
    with SessionLocal() as db:
        project = Project(name="Worker project")
        db.add(project)
        db.flush()
        job = UploadJob(
            original_filename="imagery.png",
            stored_filename=stored_filename,
            file_size=len(image_data or b""),
            content_type="image/png",
            project_name=project.name,
            project_id=project.id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job


def worker(uploads_path: Path, persistence=None, extractor=None, **options) -> ProcessingWorker:
    return ProcessingWorker(
        session_factory=SessionLocal,
        feature_persistence=persistence,
        extractor=extractor,
        upload_directory=uploads_path,
        **options,
    )


def get_job(job_id: str) -> UploadJob:
    with SessionLocal() as db:
        return db.get(UploadJob, job_id)


def test_queued_job_is_claimed_and_processed(uploads_path):
    job = create_job(uploads_path, image_data=sample_imagery())
    recorder = RecordingPersistence()

    result = worker(uploads_path, recorder).process_job(job.id)

    stored = get_job(job.id)
    assert result.status == "review"
    assert stored.status == "review"
    assert stored.processing_started_at
    assert stored.processing_completed_at
    assert len(recorder.batches) == 1


def test_claim_marks_job_processing_before_extraction(uploads_path):
    job = create_job(uploads_path, image_data=sample_imagery())
    processing_worker = worker(uploads_path)

    with SessionLocal() as db:
        claimed = processing_worker._claim(db, job.id, "test-worker", allow_retry=False)
        assert claimed.status == "processing"
        assert claimed.processing_started_at


def test_successful_extraction_outputs_building_road_and_indicative_parcel(uploads_path):
    job = create_job(uploads_path, image_data=sample_imagery())

    result = worker(uploads_path).process_job(job.id)

    feature_types = {feature["properties"]["feature_type"] for feature in result.features}
    assert {"building", "road", "parcel"}.issubset(feature_types)
    parcel = next(feature for feature in result.features if feature["properties"]["feature_type"] == "parcel")
    assert parcel["properties"]["legal_status"] == "not_a_legal_or_cadastral_boundary"


def test_worker_persists_ai_features_to_gis_for_the_upload_project(uploads_path):
    job = create_job(uploads_path, image_data=sample_imagery())

    result = worker(uploads_path).process_job(job.id)

    with SessionLocal() as db:
        persisted = db.query(GISFeature).filter_by(upload_job_id=job.id).all()
        stored_job = db.get(UploadJob, job.id)

    assert result.status == "review"
    assert stored_job.status == "review"
    assert len(persisted) == len(result.features)
    assert persisted
    assert all(feature.project_id == job.project_id for feature in persisted)
    assert all(feature.upload_job_id == job.id for feature in persisted)
    assert {feature.feature_type for feature in persisted} == {
        feature["properties"]["feature_type"] for feature in result.features
    }


def test_missing_imagery_marks_job_failed_with_reason(uploads_path):
    job = create_job(uploads_path)

    result = worker(uploads_path).process_job(job.id)

    stored = get_job(job.id)
    assert result.status == "failed"
    assert "Unable to read image" in result.failure_reason
    assert stored.failed_at
    assert stored.failure_reason == result.failure_reason


def test_failed_job_can_be_retried_explicitly(uploads_path):
    job = create_job(uploads_path)
    processing_worker = worker(uploads_path)
    assert processing_worker.process_job(job.id).status == "failed"
    (uploads_path / "imagery.png").write_bytes(sample_imagery())

    result = processing_worker.retry_job(job.id)

    stored = get_job(job.id)
    assert result.status == "review"
    assert stored.retry_count == 1
    assert stored.failure_reason is None


def test_completed_job_cannot_be_processed_twice(uploads_path):
    job = create_job(uploads_path, image_data=sample_imagery())
    processing_worker = worker(uploads_path)
    processing_worker.process_job(job.id)

    with pytest.raises(DuplicateProcessingError):
        processing_worker.process_job(job.id)


def test_invalid_generated_geometry_marks_job_failed(uploads_path):
    job = create_job(uploads_path, image_data=sample_imagery())

    result = worker(uploads_path, extractor=InvalidGeometryExtractor()).process_job(job.id)

    assert result.status == "failed"
    assert "invalid generated geometry" in result.failure_reason


def test_timeout_marks_job_failed(uploads_path):
    job = create_job(uploads_path, image_data=sample_imagery())

    result = worker(uploads_path, max_processing_seconds=0.000001).process_job(job.id)

    assert result.status == "failed"
    assert "timed out" in result.failure_reason


def test_persistence_failure_marks_job_failed_with_reason(uploads_path):
    job = create_job(uploads_path, image_data=sample_imagery())

    result = worker(uploads_path, persistence=FailingPersistence()).process_job(job.id)

    stored = get_job(job.id)
    assert result.status == "failed"
    assert stored.status == "failed"
    assert "GIS feature persistence unavailable" in result.failure_reason
    assert stored.failure_reason == result.failure_reason
