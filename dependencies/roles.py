from dependencies.auth import get_user
from database.connection import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from models.user import User

def get_client(current_user: User = Depends(get_user)):
    if current_user.role != "CLIENT":
        raise HTTPException(status_code=403, detail="You're Not Allowed")
    return current_user

def get_admin(current_user: User = Depends(get_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="You're Not Allowed")
    return current_user


def get_professional(current_user: User = Depends(get_user)):
    if current_user.role != "PROFESSIONAL":
        raise HTTPException(status_code=403, detail="You're Not Allowed")
    return current_user

def get_admin_client(current_user: User = Depends(get_user)):
    if current_user.role in ["CLIENT", "ADMIN"]:
        return current_user
    raise HTTPException(status_code=403, detail="You're Not Allowed")
    