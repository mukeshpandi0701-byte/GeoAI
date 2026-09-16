from typing import Any

from pydantic import BaseModel, Field


class GISFeatureCreate(BaseModel):
    project_id: str = Field(min_length=1)
    upload_job_id: str | None = None
    feature_type: str
    geometry: dict[str, Any]
    properties: dict[str, Any] = Field(default_factory=dict)


class GISFeatureUpdate(BaseModel):
    feature_type: str | None = None
    geometry: dict[str, Any] | None = None
    properties: dict[str, Any] | None = None
    review_status: str | None = None
    reviewer_note: str | None = Field(default=None, max_length=1000)
    reviewer: str | None = Field(default=None, max_length=160)
