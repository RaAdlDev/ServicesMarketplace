from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models.user import User
from schemas.user import UserResponse, Meta, Response
from schemas.profile import ProfileUpdate
from typing import Optional
from math import ceil
from models.profile import Profile
from models.abilitie import Abilitie

def get_me( user: User):
    return UserResponse(
        username = user.username,
        user_id= user.user_id,
        email = user.email,
        role = user.role,
        profile = user.profile)

    

def update_profile(db: Session, user: User, update_data: ProfileUpdate):
    abilities = []
    if update_data.description:
        user.profile.description = update_data.description
    if update_data.social_media:
        user.profile.social_media = update_data.social_media
    if update_data.abilities:
        abilities = db.execute(select(Abilitie).where(Abilitie.abilitie_id.in_(update_data.abilities))).scalars().all()
        user.profile.abilities = abilities
    if update_data.experience:
        user.profile.experience = update_data.experience
    db.commit()
    db.refresh(user.profile)

    return user.profile

def view_clients_professionals(db: Session, page: int, size: int,  professionals: Optional[bool] = None, clients: Optional[bool]= None, abilities: Optional[list[str]] = None, description: Optional[str] = None, username: Optional[str] = None):
    offset = (page-1)*size
    query = select(User).where(User.is_active == True)
    if clients:
        query = query.where(User.role == "CLIENT")
    if professionals:
        query = query.where(User.role == "PROFESSIONAL")
    if description:
        query = query.where(Profile.description.ilike(f"%{description}%"))
    if abilities:
        query = query.where(Profile.abilities.any(Abilitie.abilitie_id.in_(abilities)))
    if username:
        query = query.where(User.username.ilike(f"%{username}%"))

    len_items = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    if len_items < offset:
        return None
    items = db.execute(query.offset(offset).limit(size)).scalars().all()
    items_response = [None]
    if items:
        items_response =[UserResponse.model_validate(item) for item in items]
    
    total_pages =  ceil(len_items/size) if len_items > 0 else 1
    return Response(
        meta = Meta(
            total_items=  len_items,
            total_pages= total_pages,
            current_page= page,
            page_size= size,
            has_next= total_pages > page,
            has_previous= page > 1

        ),
        data= items_response
    )

def deactivate_user(db: Session, user_id: str):
    user = db.get(User, user_id)
    if not user:
        return "NOT_FOUND"
    if user.is_active == False:
        return "INVALID_STATUS"
    if user.role == "ADMIN":
        return "INVALID_ROLE"
    if user.jobs:
        for j in user.jobs:
            j.is_active = False
    user.is_active = False
    db.commit()
    return {"status": "successful request"}

def search_user(db: Session, user_id: str):
    user = db.get(User, user_id)
    if not user or user.is_active == False:
        return "NOT_FOUND"    
    return user