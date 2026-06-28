from sqlalchemy.orm import Session
from sqlalchemy import select
from models.user import User
from models.job import Job
from models.application import Application
from models.contract import Contract
from models.notification import Notification
from services.websockets_services import get_conversation

def view_my_applications(db: Session, user: User):
    applications = db.execute(select(Application).where(Application.professional_id == user.user_id)).scalars().all()
    return applications

def view_job_applications(db: Session, current_user: User, job_id: str):
    job = db.get(Job, job_id)
    if not job or job.is_active == False:
        return "NOT_FOUND"
    if job.client_id != current_user.user_id:
        return "FORBIDDEN"
    return job.applications

def accept_application(db: Session, current_user: User, application_id: str, message: str):
    application = db.get(Application, application_id)
    if not application:
        return "NOT_FOUND"
    job = db.get(Job, application.job_id)
    if application.status != "PENDING":         
        return "INVALID_STATUS"
    if not job or job.is_active == False:
        return "NOT_FOUND"
    if job.client_id != current_user.user_id:
        return "FORBIDDEN"
    contract = Contract(
        job_id = job.job_id,
        seller_id = application.professional_id,
        buyer_id = job.client_id,
        detail = job.description,
        amount = job.budget)
    
    notification = Notification(
        sender_id = current_user.user_id,
        message = message,
        conversation_id = get_conversation(db, current_user.user_id, application.professional_id)
    )
    job.is_active = False
    application.status = "ACEPTED"
    db.add(contract)
    db.add(notification)
    db.commit()
    db.refresh(contract)
    db.refresh(notification)

    return contract, notification

