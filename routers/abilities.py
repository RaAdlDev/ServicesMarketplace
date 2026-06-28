from fastapi import APIRouter, Depends, HTTPException
from database.connection import get_db
from dependencies.roles import get_admin
from dependencies.auth import get_user
from models.user import User
from sqlalchemy.orm import Session
from schemas.abilities import AbilitiesInput, AbilitiesResponse
from services.abilities_services import post_abilitie, view_abilities

router = APIRouter(prefix="/abilities", tags=["Abilities"])


@router.post("", response_model=AbilitiesResponse)
async def new_abilitie(abilitie_data: AbilitiesInput, current_user: User = Depends(get_admin), db: Session = Depends(get_db)):
    status = post_abilitie(db, abilitie_data)
    if status is None:
        raise HTTPException(status_code=409, detail="The Abilitie Already Exists")
    return status

@router.get("", response_model=list[AbilitiesResponse])
async def get_abilities(current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    return view_abilities(db)
 