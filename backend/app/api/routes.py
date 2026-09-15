from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.project_service import (
    UploadStorageError,
    create_upload_job,
    get_upload_job,
    validate_image_file,
)

router = APIRouter(tags=["uploads"])

@router.post("/uploads/drone-image", status_code=202)
async def upload_drone_image(file: UploadFile = File(...), project_name: str = Form(...)):
    if not project_name.strip():
        raise HTTPException(status_code=422, detail="A project name is required.")
    try:
        validate_image_file(file)
        return await create_upload_job(file=file, project_name=project_name)
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
    except UploadStorageError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        await file.close()


@router.get("/uploads/{job_id}")
def upload_status(job_id: str):
    job = get_upload_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found.")
    return job
