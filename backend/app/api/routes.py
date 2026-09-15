from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.project import ProjectCreate
from app.db.models import Project, UploadJob, utc_now
from app.services.project_service import upload_job_response

from app.services.project_service import (
    UploadStorageError,
    ProjectNotFoundError,
    create_upload_job,
    get_upload_job,
    validate_image_file,
)
from app.services.projects_service import create_project, get_project, list_projects

router = APIRouter()
@router.patch("/review-queue/{job_id}", tags=["review"])
def update_review_status(
    job_id: str,
    decision: str,
    db: Session = Depends(get_db),
):
    if decision not in {"approved", "rejected"}:
        raise HTTPException(
            status_code=400,
            detail="Decision must be approved or rejected.",
        )

    job = db.get(UploadJob, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Review job not found.",
        )

    job.status = decision
    job.reviewed_at = utc_now()
    if job.project:
        job.project.status = "published" if decision == "approved" else "rejected"
    db.commit()
    db.refresh(job)

    return upload_job_response(job)
@router.get("/review-queue", tags=["review"])
def review_queue(
    status: str = Query(default="review"),
    db: Session = Depends(get_db),
):
    if status not in {"review", "approved", "rejected"}:
        raise HTTPException(
            status_code=400,
            detail="Status must be review, approved, or rejected.",
        )
    jobs = (
        db.query(UploadJob)
        .filter(UploadJob.status == status)
        .order_by(UploadJob.created_at.desc())
        .all()
    )

    return [upload_job_response(job) for job in jobs]
@router.post("/uploads/drone-image", status_code=202, tags=["uploads"])
async def upload_drone_image(
    file: UploadFile = File(...),
    project_name: str = Form(...),
    project_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    if not project_name.strip():
        raise HTTPException(status_code=422, detail="A project name is required.")
    try:
        validate_image_file(file)
        return await create_upload_job(
            db=db,
            file=file,
            project_name=project_name,
            project_id=project_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except UploadStorageError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        await file.close()


@router.get("/uploads/{job_id}", tags=["uploads"])
def upload_status(job_id: str, db: Session = Depends(get_db)):
    job = get_upload_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found.")
    return job


@router.post("/projects", status_code=201, tags=["projects"])
def create_project_endpoint(project: ProjectCreate, db: Session = Depends(get_db)):
    if not project.name.strip():
        raise HTTPException(status_code=422, detail="A project name is required.")
    return create_project(db, project)


@router.get("/projects", tags=["projects"])
def project_list(db: Session = Depends(get_db)):
    return list_projects(db)


@router.get("/projects/{project_id}", tags=["projects"])
def project_lookup(project_id: str, db: Session = Depends(get_db)):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.get("/projects/{project_id}/uploads", tags=["projects"])
def project_upload_history(project_id: str, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    jobs = (
        db.query(UploadJob)
        .filter(UploadJob.project_id == project_id)
        .order_by(UploadJob.created_at.desc())
        .all()
    )
    return [upload_job_response(job) for job in jobs]
