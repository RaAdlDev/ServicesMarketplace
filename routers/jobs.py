from fastapi import APIRouter, Depends, HTTPException, Query
from dependencies.auth import get_user
from dependencies.roles import get_client, get_professional, get_admin, get_admin_client
from models.user import User
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.jobs import JobInput, JobResponse, JobUpdate, PaginationJob
from services.jobs_services import add_job, view_jobs, view_one_job, send_proposal, deactivate_job, edit_job, view_my_jobs
from decimal import Decimal
from typing import Optional
from schemas.application import AplicationInput

router = APIRouter(prefix="/jobs", tags=['Jobs'])

@router.post("", response_model=JobResponse)
async def new_job(job_data: JobInput, current_user: User = Depends(get_client), db: Session = Depends(get_db)):
    return add_job(db, current_user, job_data)

@router.get("", response_model= PaginationJob[JobResponse])
async def get_jobs( current_user: User = Depends(get_user), db: Session = Depends(get_db), page: int = Query(1, ge=1, description="Jobs Page"), size: int = Query(10, ge=1, le=100, description="Jobs Page Size"), search: Optional[str] = Query(None), abilities: Optional[list[str]]= Query(None), budget: Optional[Decimal]= Query(None)):
    status = view_jobs(db, size, page, abilities, search, budget )
    if status is None:
        raise HTTPException(status_code=409, detail="The Page Is Too Large")
    return status

@router.get("/my-jobs", response_model=list[JobResponse])
async def get_my_jobs( current_user: User = Depends(get_client), db: Session = Depends(get_db)):
    return view_my_jobs(db, current_user)

@router.get("/{job_id}", response_model=JobResponse)
async def get_one_job(job_id: str, current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    status = view_one_job(db, job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job Not Found")
    return status
    
@router.post("/{job_id}/apply")
async def apply_job( job_id: str, proposal:AplicationInput, current_user: User = Depends(get_professional), db: Session = Depends(get_db)):
    status = send_proposal(db, current_user, job_id, proposal)
    if status is None:
        raise HTTPException(status_code=404, detail="Job Not Found")
    if status == "FORBIDDEN":
        raise HTTPException(status_code=409, detail="You Have Already Apply")
    return status

@router.delete("/{job_id}/delete")
async def delete_job(job_id: str, current_user: User = Depends(get_admin_client), db: Session = Depends(get_db)):
    status = deactivate_job(db, current_user, job_id)
    if status == "FORBIDDEN":
        raise HTTPException(status_code=409, detail="You're Not Allowed")
    if status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Job Not Found")
    return status

@router.patch("/{job_id}/update", response_model=JobResponse)
async def update_job(job_id: str, job_data: JobUpdate, current_user: User = Depends(get_client), db: Session = Depends(get_db)):
    status = edit_job(db, current_user, job_id, job_data)
    if status == "FORBIDDEN":
        raise HTTPException(status_code=409, detail="You're Not Allowed")
    if status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Job Not Found")
    return status




