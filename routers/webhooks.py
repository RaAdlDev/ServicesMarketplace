from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from database.connection import get_db
from sqlalchemy.orm import Session
import stripe
from core.settings import settings
from services.webhooks_services import guarantee_contract, contract_paid, contract_failed, contract_refund, contract_disputed
router = APIRouter(prefix="/webhook", tags=["Webhooks"])


@router.post("/stripe")
async def get_webhook( background: BackgroundTasks, request: Request, db: Session = Depends(get_db) ):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload invalido")
    except stripe.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Stripe Error {e}")
    except stripe.StripeError:
        raise HTTPException(status_code=400, detail="Stripe Server Error")
    
    data_object = event.data.object
    
    if event.type == "payment_intent.succeeded":
        contract_id = data_object.get("metadata", {}).get("contract_id")
        if contract_id:
            charge_id = data_object.get("latest_charge")
            background.add_task(guarantee_contract,background, contract_id, charge_id)


    elif event.type == "transfer.created":
        contract_id = data_object.get("metadata", {}).get("contract_id")
        if contract_id:
            background.add_task(contract_paid, background, contract_id)

    elif event.type == "payment_intent.payment_failed":
        contract_id = data_object.get("metadata", {}).get("contract_id")
        if contract_id:
            background.add_task(contract_failed,background, contract_id)
    elif event.type == "charge.refunded":
        contract_id = data_object.get("metadata", {}).get("contract_id")
        if contract_id:
            refund_id = data_object.get("refunds", {}).get("data", [{}])[0].get("id")
            background.add_task(contract_refund,background, contract_id, refund_id)
    elif event.type == "charge.dispute.created":
        charge_id = data_object.get("charge")
        background.add_task(contract_disputed,background, charge_id)
    

    return {"status": "successful"}