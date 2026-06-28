from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from services.auth_services import register_user, login_user
from schemas.user import UserRegister, UserLogin


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def new_user(user_data: UserRegister, db: Session = Depends(get_db)):
    status = register_user(db, user_data)
    if status is None:
        raise HTTPException(status_code=409, detail="Try Another Data")
    if status == "INTERNAL_SERVER_ERROR":
        raise HTTPException(status_code=500, detail="Internal Server Error")
    if status == "STRIPE_ERROR":
        raise HTTPException(status_code=400, detail="Stripe Server Error")
    return status

@router.post("/login")
async def authenticate_user(user_data: UserLogin, db: Session = Depends(get_db)):
    status = login_user(db, user_data)
    if status is None:
        raise HTTPException(status_code=401, detail="Invalid Data")
    return status
