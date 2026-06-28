from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from dependencies.roles import get_client, get_professional
from models.user import User
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.application import AplicationResponse, ApplicationAcepted
from services.applications_services import view_my_applications, view_job_applications, accept_application
from services.websockets_services import send_notification
from schemas.contract import ContractResponse

router = APIRouter(prefix="/application", tags=["Applications"])

@router.get("/my-applications", response_model=list[AplicationResponse])
async def get_my_applications( current_user: User = Depends(get_professional), db: Session = Depends(get_db)):
    return view_my_applications(db, current_user)

@router.get("/{job_id}", response_model=list[AplicationResponse])
async def get_my_jobs_applications( job_id: str, current_user: User = Depends(get_client), db: Session = Depends(get_db)):
    status = view_job_applications(db, current_user, job_id)
    if status == "FORBIDDEN":
        raise HTTPException(status_code=409, detail="Is Not Your Job")
    if status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Job Not Found")
    return status
@router.post("/{application_id}/accept", response_model=ContractResponse)
async def accept_job_application(background: BackgroundTasks, message: ApplicationAcepted, application_id: str, current_user: User = Depends(get_client), db: Session = Depends(get_db)):
    status = accept_application(db, current_user, application_id, message.message)
    if status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Application Not Found")
    if status == "FORBIDDEN":
        raise HTTPException(status_code=409, detail="Not Allowed")
    if status == "INVALID_STATUS":
        return HTTPException(status_code=409, detail= "Invalid Status")
    contract, notification = status
    background.add_task(send_notification, notification)
    return contract

