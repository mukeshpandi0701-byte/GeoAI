from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import GISFeature, Project, UploadJob
from app.models.project import ProjectCreate
from app.services.project_service import upload_job_response


def project_response(project: Project, db: Session) -> dict:
    """Keep the established frontend project response field names."""
    status_counts = dict(
        db.execute(
            select(UploadJob.status, func.count())
            .where(UploadJob.project_id == project.id)
            .group_by(UploadJob.status)
        ).all()
    )
    return {
        "project_id": project.id,
        "project_name": project.name,
        "description": project.description,
        "location": project.location,
        "created_timestamp": project.created_at.isoformat(),
        "status": project.status,
        "upload_summary": {
            "total": sum(status_counts.values()),
            "queued": status_counts.get("queued", 0),
            "processing": status_counts.get("processing", 0),
            "review": status_counts.get("review", 0),
            "failed": status_counts.get("failed", 0),
            "approved": status_counts.get("approved", 0),
            "rejected": status_counts.get("rejected", 0),
        },
    }


def create_project(db: Session, details: ProjectCreate) -> dict:
    """Persist a project and return its API representation."""
    project = Project(
        name=details.name.strip(),
        description=details.description.strip(),
        location=details.location.strip(),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_response(project, db)


def list_projects(db: Session) -> list[dict]:
    """Return persisted projects newest first."""
    statement = select(Project).order_by(Project.created_at.desc())
    return [project_response(project, db) for project in db.scalars(statement)]


def get_project(db: Session, project_id: str) -> dict | None:
    """Look up one persisted project."""
    project = db.get(Project, project_id)
    return project_response(project, db) if project else None


def project_processing_history(db: Session, project_id: str) -> list[dict] | None:
    """Return a project's durable jobs with their persisted feature totals."""
    if not db.get(Project, project_id):
        return None

    feature_counts = dict(
        db.execute(
            select(GISFeature.upload_job_id, func.count())
            .where(GISFeature.project_id == project_id)
            .group_by(GISFeature.upload_job_id)
        ).all()
    )
    jobs = db.scalars(
        select(UploadJob)
        .where(UploadJob.project_id == project_id)
        .order_by(UploadJob.created_at.desc())
    )
    return [
        upload_job_response(job) | {"feature_count": feature_counts.get(job.id, 0)}
        for job in jobs
    ]
