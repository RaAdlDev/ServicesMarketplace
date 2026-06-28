from fastapi import APIRouter, Depends, HTTPException
from dependencies.auth import get_user
from dependencies.roles import get_client
from models.user import User
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.contract import ContractResponse
from services.contract_services import view_contracts, guaranteed_contract, contract_fullfiled, reject_contrat

router = APIRouter(prefix="/contracts")


@router.get("", response_model=list[ContractResponse])
async def get_my_contracts(db: Session = Depends(get_db), current_user: User = Depends(get_user)):
    return view_contracts(db, current_user)

@router.post("/{contract_id}/pay")
async def pay_contracts( contract_id: str,  db: Session = Depends(get_db), current_user: User = Depends(get_client)):
    status = guaranteed_contract(db, contract_id, current_user)
    if status == "INTERNAL_SERVER_ERROR":
        raise HTTPException(status_code=500, detail="Internal Server Error")
    if status == "INVALID_STATUS":
        raise HTTPException(status_code=409, detail="Invalid Contract Status")
    if status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail= "Contract Not Found")
    if status == "STRIPE_ERROR":
        raise HTTPException(status_code=400, detail="Stripe Server Error")
    if status == "FORBIDDEN":
        raise HTTPException(status_code=409, detail="The Contract Is Not Yours")

    return status

@router.post("/{contract_id}/refund")
async def refound_contract( contract_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_client)):
    status = reject_contrat(db, contract_id, current_user)
    if status == "INTERNAL_SERVER_ERROR":
        raise HTTPException(status_code=500, detail="Internal Server Error")
    if status == "INVALID_STATUS":
        raise HTTPException(status_code=409, detail="Invalid Contract Status")
    if status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail= "Contract Not Found")
    if status == "STRIPE_ERROR":
        raise HTTPException(status_code=400, detail="Stripe Server Error")
    if status == "FORBIDDEN":
        raise HTTPException(status_code=409, detail="The Contract Is Not Yours")
    return status


@router.post("/{contract_id}/completed")
async def completed_contract( contract_id: str,  db: Session = Depends(get_db), current_user: User = Depends(get_client)):
    status = contract_fullfiled(db, contract_id, current_user)
    
    if status == "INTERNAL_SERVER_ERROR":
        raise HTTPException(status_code=500, detail="Internal Server Error")
    if status == "INVALID_STATUS":
        raise HTTPException(status_code=409, detail="Invalid Contract Status")
    if status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail= "Contract Not Found")
    if status == "SELLER_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Seller Not Found")
    if status == "STRIPE_ERROR":
        raise HTTPException(status_code=400, detail="Stripe Server Error")
    if status == "FORBIDDEN":
        raise HTTPException(status_code=409, detail="The Contract Is Not Yours")
    return status
 