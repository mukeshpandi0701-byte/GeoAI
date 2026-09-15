from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.project import ProjectCreate

from app.services.project_service import (
    UploadStorageError,
    create_upload_job,
    get_upload_job,
    validate_image_file,
)
from app.services.projects_service import create_project, get_project, list_projects

router = APIRouter()

@router.post("/uploads/drone-image", status_code=202, tags=["uploads"])
async def upload_drone_image(
    file: UploadFile = File(...),
    project_name: str = Form(...),
    db: Session = Depends(get_db),
):
    if not project_name.strip():
        raise HTTPException(status_code=422, detail="A project name is required.")
    try:
        validate_image_file(file)
        return await create_upload_job(db=db, file=file, project_name=project_name)
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
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
