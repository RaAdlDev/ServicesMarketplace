from fastapi import APIRouter, Depends, HTTPException, Query
from dependencies.auth import get_user
from dependencies.roles import get_admin
from models.user import User
from sqlalchemy.orm import Session
from database.connection import get_db
from services.user_services import get_me, update_profile, view_clients_professionals, deactivate_user, search_user
from schemas.profile import ProfileUpdate, ProfileResponse
from typing import Optional
from schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=['Users'])

@router.get("/me")
async def get_current(current_user: User = Depends(get_user)):
    return get_me(current_user)

@router.patch("/me", response_model=ProfileResponse)
async def patch_current_profile(update_data: ProfileUpdate, current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    return update_profile(db, current_user, update_data)

@router.get("/clients")
async def get_clients(current_user: User = Depends(get_user), db: Session = Depends(get_db), page: int = Query(1, ge=1, description="Page number"), size: int = Query(10, ge=1, le=100, description="Page size"), description: Optional[str] = None, username: Optional[str] = None):
    status = view_clients_professionals(db, page, size, clients=True, username=username, description=description)
    if status is None:
        raise HTTPException(status_code=409, detail="The Page Is Too Large")
    return status

@router.get("/professionals")
async def get_professionals(current_user: User = Depends(get_user), db: Session = Depends(get_db),  page: int = Query(1, ge=1, description="Page number"), size: int = Query(10, ge=1, le=100, description="Page size"), username: Optional[str] = None, abilities: Optional[str] = None, description: Optional[str] = None):
    status = view_clients_professionals(db, page, size, professionals=True, abilities = abilities, description= description, username=username )
    if status is None:
        raise HTTPException(status_code=409, detail="The Page Is Too Large")
    return status


@router.get("/{user_id}", response_model=UserResponse)
async def get_one_user(user_id: str, current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    status = search_user(db, user_id)
    if status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Not Found")
    return status

@router.delete("/{user_id}/deactivate")
async def user_out(user_id: str, current_user: User = Depends(get_admin), db: Session = Depends(get_db)):
    status = deactivate_user(db, user_id)
    if status == "INVALID_STATUS":
        raise HTTPException(status_code=409, detail="The User Is Already Inactive")
    if status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="User Not Found")
    if status =="INVALID_ROLE":
        raise HTTPException(status_code=409, detail="The User Is An Admin")
    return status
 