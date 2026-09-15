from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Project
from app.models.project import ProjectCreate


def project_response(project: Project) -> dict:
    """Keep the established frontend project response field names."""
    return {
        "project_id": project.id,
        "project_name": project.name,
        "description": project.description,
        "location": project.location,
        "created_timestamp": project.created_at.isoformat(),
        "status": project.status,
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
    return project_response(project)


def list_projects(db: Session) -> list[dict]:
    """Return persisted projects newest first."""
    statement = select(Project).order_by(Project.created_at.desc())
    return [project_response(project) for project in db.scalars(statement)]


def get_project(db: Session, project_id: str) -> dict | None:
    """Look up one persisted project."""
    project = db.get(Project, project_id)
    return project_response(project) if project else None
