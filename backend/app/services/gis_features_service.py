"""Persistence and review operations for AI-assisted physical GIS features."""

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.ai.feature_handoff import ExtractedFeatureBatch, FeaturePersistencePort
from app.db.database import SessionLocal
from app.db.models import GISFeature, Project, UploadJob
from app.gis.geometry import create_feature as make_feature
from app.gis.spatial_validation import ensure_no_polygon_self_intersection, overlap_warnings
from app.models.gis_feature import GISFeatureCreate, GISFeatureUpdate

REVIEW_STATUSES = {"pending", "accepted", "rejected"}


class GISFeaturePersistenceAdapter(FeaturePersistencePort):
    """Persist validated AI output through the established GIS feature service."""

    def __init__(self, session_factory: sessionmaker = SessionLocal) -> None:
        self.session_factory = session_factory

    def persist(self, batch: ExtractedFeatureBatch) -> None:
        if not batch.project_id:
            raise ValueError("AI feature persistence requires an associated project.")

        with self.session_factory() as db:
            for feature in batch.features:
                properties = feature.get("properties")
                if not isinstance(properties, dict):
                    raise ValueError("AI feature persistence requires feature properties.")
                feature_type = properties.get("feature_type")
                if not isinstance(feature_type, str):
                    raise ValueError("AI feature persistence requires a feature type.")
                create_feature(
                    db,
                    GISFeatureCreate(
                        project_id=batch.project_id,
                        upload_job_id=batch.upload_job_id,
                        feature_type=feature_type,
                        geometry=feature.get("geometry"),
                        properties=properties,
                    ),
                )


def _json(value: str):
    return json.loads(value)


def feature_response(feature: GISFeature) -> dict:
    response = make_feature(feature.feature_type, _json(feature.geometry_json), _json(feature.properties_json))
    response["id"] = feature.id
    response.update({
        "project_id": feature.project_id,
        "upload_job_id": feature.upload_job_id,
        "review_status": feature.review_status,
        "reviewer_note": feature.reviewer_note,
        "reviewer": feature.reviewer,
        "reviewed_at": feature.reviewed_at.isoformat() if feature.reviewed_at else None,
        "created_timestamp": feature.created_at.isoformat(),
        "updated_timestamp": feature.updated_at.isoformat(),
        "validation_warnings": _json(feature.validation_warnings_json),
    })
    return response


def _ensure_associations(db: Session, project_id: str, upload_job_id: str | None) -> None:
    if not db.get(Project, project_id):
        raise ValueError("Project not found.")
    if upload_job_id:
        upload = db.get(UploadJob, upload_job_id)
        if not upload:
            raise ValueError("Upload job not found.")
        if upload.project_id and upload.project_id != project_id:
            raise ValueError("Upload job does not belong to the project.")


def _validated_values(db: Session, project_id: str, feature_type: str, geometry: dict, properties: dict, exclude_id: str | None = None) -> tuple[dict, dict, list[str]]:
    shape = make_feature(feature_type, geometry, properties)
    ensure_no_polygon_self_intersection(shape["geometry"])
    statement = select(GISFeature).where(GISFeature.project_id == project_id)
    if exclude_id:
        statement = statement.where(GISFeature.id != exclude_id)
    existing = list(db.scalars(statement))
    for item in existing:
        if item.feature_type == feature_type and _json(item.geometry_json) == shape["geometry"]:
            raise ValueError("Duplicate feature geometry already exists in this project.")
    warnings = overlap_warnings(feature_type, shape["geometry"], [(item.feature_type, _json(item.geometry_json)) for item in existing])
    return shape["geometry"], properties, warnings


def create_feature(db: Session, details: GISFeatureCreate) -> dict:
    _ensure_associations(db, details.project_id, details.upload_job_id)
    geometry, properties, warnings = _validated_values(db, details.project_id, details.feature_type, details.geometry, details.properties)
    feature = GISFeature(project_id=details.project_id, upload_job_id=details.upload_job_id, feature_type=details.feature_type, geometry_json=json.dumps(geometry), properties_json=json.dumps(properties), validation_warnings_json=json.dumps(warnings))
    db.add(feature)
    db.commit()
    db.refresh(feature)
    return feature_response(feature)


def get_feature(db: Session, feature_id: str) -> dict | None:
    feature = db.get(GISFeature, feature_id)
    return feature_response(feature) if feature else None


def list_features(db: Session, project_id: str | None = None, upload_job_id: str | None = None, feature_type: str | None = None, review_status: str | None = None) -> list[dict]:
    statement = select(GISFeature).order_by(GISFeature.created_at.desc())
    if project_id:
        statement = statement.where(GISFeature.project_id == project_id)
    if upload_job_id:
        statement = statement.where(GISFeature.upload_job_id == upload_job_id)
    if feature_type:
        statement = statement.where(GISFeature.feature_type == feature_type)
    if review_status:
        statement = statement.where(GISFeature.review_status == review_status)
    return [feature_response(feature) for feature in db.scalars(statement)]


def update_feature(db: Session, feature_id: str, changes: GISFeatureUpdate) -> dict | None:
    feature = db.get(GISFeature, feature_id)
    if not feature:
        return None
    values = changes.model_dump(exclude_unset=True)
    feature_type = values.get("feature_type", feature.feature_type)
    geometry = values.get("geometry", _json(feature.geometry_json))
    properties = values.get("properties", _json(feature.properties_json))
    if {"feature_type", "geometry", "properties"} & values.keys():
        normalized_geometry, normalized_properties, warnings = _validated_values(db, feature.project_id, feature_type, geometry, properties, feature.id)
        feature.feature_type = feature_type
        feature.geometry_json = json.dumps(normalized_geometry)
        feature.properties_json = json.dumps(normalized_properties)
        feature.validation_warnings_json = json.dumps(warnings)
    if "review_status" in values:
        if values["review_status"] not in REVIEW_STATUSES:
            raise ValueError("Review status must be pending, accepted, or rejected.")
        feature.review_status = values["review_status"]
        feature.reviewed_at = datetime.now(timezone.utc) if values["review_status"] != "pending" else None
    for field in ("reviewer_note", "reviewer"):
        if field in values:
            setattr(feature, field, values[field] or "")
    db.commit()
    db.refresh(feature)
    return feature_response(feature)


def delete_feature(db: Session, feature_id: str) -> bool:
    feature = db.get(GISFeature, feature_id)
    if not feature:
        return False
    db.delete(feature)
    db.commit()
    return True
