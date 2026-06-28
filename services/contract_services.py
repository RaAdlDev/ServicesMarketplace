from sqlalchemy.orm import Session 
from sqlalchemy import select, or_
from models.user import User
from models.contract import Contract
import stripe

def view_contracts(db: Session, current_user: User):
    contracts = db.execute(select(Contract).where(or_(
        Contract.seller_id == current_user.user_id,
        Contract.buyer_id == current_user.user_id
    ))).scalars().all()
    return contracts


def guaranteed_contract(db: Session,  contract_id: str, current_user: User):
    contract = db.get(Contract, contract_id)
    if not contract:
        return "NOT_FOUND"
    if not contract.buyer_id == current_user.user_id:
        return "FORBIDDEN"
    if contract.status != "PENDING_PAYMENT":
        return "INVALID_STATUS"
    amount = int(round(contract.amount * 100))
    try: 
        transaction_intent = stripe.PaymentIntent.create(
            amount= amount,
            currency="usd",
            payment_method_types=["card"],
            metadata = {
                "contract_id": contract.contract_id,
                                            })
        contract.payment_intent_id = transaction_intent.id
        status = {"payment_intent_id": transaction_intent.id,
                  "client_secret": transaction_intent.client_secret,
                  "status": "payment guaranteed"}

        db.commit()
        return status
    except stripe.StripeError :
        db.rollback()
        return "STRIPE_ERROR"
    except Exception:
        db.rollback()
        return "INTERNAL_SERVER_ERROR"


def reject_contrat(db: Session,  contract_id: str, current_user: User):
    contract = db.get(Contract, contract_id)
    if not contract:
        return "NOT_FOUND"
    if not contract.buyer_id == current_user.user_id:
        return "FORBIDDEN"
    if contract.status !=  "GUARANTEED":
        return "INVALID_STATUS"

    amount = int(round(contract.amount * 100))
    try: 
        stripe.Refund.create(
            amount= amount,
            payment_intent= contract.payment_intent_id,
            metadata= {
                "contract_id": contract.contract_id
            }
        )
        
        db.commit()
        return{"status": "successful refund"}
    except stripe.StripeError:
        return "STRIPE_ERROR"
    except Exception:
        return "INTERNAL_SERVER_ERROR"

def contract_fullfiled(db: Session,  contract_id: str, current_user: User):
    contract = db.get(Contract, contract_id)
    if not contract:
        return "NOT_FOUND"
    if not contract.buyer_id == current_user.user_id:
        return "FORBIDDEN"
    if contract.status != "GUARANTEED":
        return "INVALID_STATUS"
    seller = db.get(User, contract.seller_id)
    if not seller or seller.is_active == False:
        return "SELLER_NOT_FOUND"
    amount = int(round(contract.amount * 100))
    try: 
        transfer = stripe.Transfer.create(
            amount= amount,
            currency= "usd",
            destination= seller.stripe_connect_id,
            source_transaction= contract.charge_id,
            metadata= {
                "contract_id": contract.contract_id
            }
        )
        status = {
            "status": "funds released successfuly",
            "transfer_id": transfer.id,
            "destination": seller.stripe_connect_id}
        
        db.commit()
        return status
    except stripe.StripeError:
        return "STRIPE_ERROR"
    except Exception:
        return "INTERNAL_SERVER_ERROR"
 