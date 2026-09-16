from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    location: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    upload_jobs: Mapped[list["UploadJob"]] = relationship(back_populates="project")
    gis_features: Mapped[list["GISFeature"]] = relationship(back_populates="project")


class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    # Retained for the existing upload API, which currently submits a project name.
    project_name: Mapped[str] = mapped_column(String(120), nullable=False)

    project: Mapped[Project | None] = relationship(back_populates="upload_jobs")
    gis_features: Mapped[list["GISFeature"]] = relationship(back_populates="upload_job")


class GISFeature(Base):
    """An AI-mapped physical feature, never an official cadastral record."""

    __tablename__ = "gis_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    upload_job_id: Mapped[str | None] = mapped_column(ForeignKey("upload_jobs.id"), nullable=True, index=True)
    feature_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    geometry_json: Mapped[str] = mapped_column(Text, nullable=False)
    properties_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    validation_warnings_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    reviewer_note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reviewer: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project: Mapped[Project] = relationship(back_populates="gis_features")
    upload_job: Mapped[UploadJob | None] = relationship(back_populates="gis_features")
