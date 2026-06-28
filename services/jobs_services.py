from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from schemas.jobs import JobInput, MetaJobs, PaginationJob, JobUpdate
from models.job import Job
from models.user import User
from typing import Optional
from models.abilitie import Abilitie
from decimal import Decimal
from math import ceil
from models.application import Application
from schemas.application import AplicationInput


def add_job(db: Session, user: User, job_data: JobInput):
    new_job = Job(
        title = job_data.title,
        description = job_data.description,
        client_id = user.user_id,
        budget = job_data.budget
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job

def view_jobs(db: Session, size: int, page: int, abilities: Optional[list[str]] = None, search: Optional[str] = None, budget: Optional[Decimal] = None):
    offset = (page - 1)* size
    query = select(Job).where(Job.is_active == True)
    if abilities:
        query = query.where(Job.abilities.any(Abilitie.abilitie_id.in_(abilities)))
    if search:
        query = query.where(or_(Job.description.ilike(f"%{search}%"), Job.title.ilike(f"%{search}%")))
    if budget:
        query = query.where(Job.budget <= budget)

    len_items = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    if len_items < offset:
        return None
    items = db.execute(query.offset(offset).limit(size)).scalars().all()
    total_pages = ceil(len_items / size) if len_items > 0 else 1

    return PaginationJob(
        meta =    MetaJobs(
        total_pages= total_pages,
        total_items= len_items,
        page_size= size,
        current_page=page,
        has_previous= page > 1,
        has_next= total_pages > page),
        data= items
    )

def view_one_job(db: Session, job_id: str):
    job = db.get(Job, job_id)
    if not job or job.is_active == False:
        return None
    return job

def send_proposal(db: Session, current_user: User, job_id: str, application_data: AplicationInput):
    verify_applications = db.execute(select(Application).where(Application.job_id == job_id, Application.professional_id == current_user.user_id)).scalar_one_or_none()
    if verify_applications:
        return "FORBIDDEN"
    job = db.get(Job, job_id)
    if not job or job.is_active == False:
        return None

    new_application = Application(
        professional_id = current_user.user_id,
        abilities_description = application_data.abilities_description,
        proposal = application_data.proposal,
        cv = application_data.cv if application_data.cv else None,
        job_id = job.job_id)
    db.add(new_application)
    job.requests = job.requests + 1
    db.commit()

    return {"status": "successful request"}

def deactivate_job(db: Session, current_user: User, job_id: str):
    job_out = db.get(Job, job_id)
    if not job_out or job_out.is_active == False:
        return "NOT_FOUND"
    if current_user.role == "CLIENT": 
        if job_out.client_id != current_user.user_id:
            return "FORBIDDEN"
    job_out.is_active = False
    db.commit()
    return {"status": "successful request"}

def edit_job(db: Session, current_user: User, job_id: str, job_data: JobUpdate):
    job = db.get(Job, job_id)
    if not job or job.is_active == False:
        return "NOT_FOUND"
    if job.client_id != current_user.user_id:
        return "FORBIDDEN"
    if job_data.budget:
        job.budget = job_data.budget
    if job_data.description:
        job.description = job_data.description
    if job_data.title:
        job.title = job_data.title
    db.commit()
    db.refresh(job)

    return job

def view_my_jobs(db: Session, current_user: User):
    return db.execute(select(Job).where(Job.client_id == current_user.user_id)).scalars().all()