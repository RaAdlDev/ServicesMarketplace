from sqlalchemy.orm import sessionmaker
from fastapi import BackgroundTasks
from models.contract import Contract
from database.connection import engine
from models.notification import Notification
from models.user import User
from services.websockets_services import get_conversation, send_notification
import logging
from sqlalchemy import select
LocalSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def guarantee_contract(background: BackgroundTasks, contract_id: str, charge_id: str ):
    with LocalSession() as db:
        try:
            contract = db.get(Contract, contract_id)
            if not contract:
                logging.error(f"Webhhok Error: Contract {contract_id}, not found")
                return
            if contract.status == "PENDING_PAYMENT":
                contract.status = "GUARANTEED"
                contract.charge_id = charge_id
                user = db.get(User, contract.buyer_id)
                new_notification = Notification(
                conversation_id = get_conversation(db, contract.seller_id, contract.buyer_id),
                message = f"The payment of the following contract {contract.contract_id} have been guaranteed",
                    sender_id = user.user_id)
                db.add(new_notification)
                db.commit()
                db.refresh(new_notification)
                background.add_task(send_notification, new_notification)
                logging.error(f"Payment of {contract_id} Contract Have Been Guaranteed Succesfully")
        except Exception as e:
            db.rollback()
            logging.error(f"error while processing payment {e}")

def contract_paid(background: BackgroundTasks, contract_id: str):
    with LocalSession() as db:
        try:
            contract = db.get(Contract, contract_id)
            if not contract or contract.status != "GUARANTEED":
                logging.error(f"Webhhok Error: Contract {contract_id}, not found")
                return None
            contract.status = "COMPLETED"
            user = db.get(User, contract.buyer_id)
            new_notification = Notification(
            conversation_id = get_conversation(db, contract.seller_id, contract.buyer_id),
            message = f"The payment of the following contract {contract.contract_id} have been completed, the projest is done",
            sender_id = user.user_id)
            db.add(new_notification)
            db.commit()
            db.refresh(new_notification)
            background.add_task(send_notification, new_notification)
            logging.info(f"Payment of {contract_id} Contract Have Been Completed Succesfully")
        except Exception as e:
            db.rollback()
            logging.error("error while processing payment transfer")

def contract_failed(background: BackgroundTasks, contract_id: str):
    with LocalSession() as db:
        try:
            contract = db.get(Contract, contract_id)
            if not contract:
                logging.error(f"Webhhok Error: Contract {contract_id}, not found")
                return
            user = db.get(User, contract.buyer_id)
            if contract.status == "PENDING_PAYMENT":
                contract.status = "FAILED"
                new_notification = Notification(
                conversation_id = get_conversation(db, contract.seller_id, contract.buyer_id),
                message = f"The payment of the following contract {contract.contract_id} have been failed",
                sender_id = user.user_id)
                db.add(new_notification)
                db.commit()
                db.refresh(new_notification)
                background.add_task(send_notification, new_notification)
        except Exception as e:
            logging.error(f"error while procesing payment {e}")


def contract_refund(background: BackgroundTasks,contract_id: str, refund_id: str):
    with LocalSession() as db:
        try:
            contract = db.get(Contract, contract_id)
            if not contract:
                logging.error(f"Webhhok Error: Contract {contract_id}, not found")
                return
            if contract.status == "GUARANTEED":
                contract.status = "REFUNDED"
                contract.refund_id = refund_id
                user = db.get(User, contract.buyer_id)
                new_notification = Notification(
                conversation_id = get_conversation(db, contract.seller_id, contract.buyer_id),
                message = f"The payment of the following contract {contract.contract_id} have been canceled, don't continue or start with the project",
                sender_id = user.user_id
                )
                db.add(new_notification)
                db.commit()
                db.refresh(new_notification)
                background.add_task(send_notification, new_notification)
        except Exception as e:
            logging.error(f"error while procesing refund {e}")

def contract_disputed(background: BackgroundTasks, charge_id: str):
    with LocalSession() as db:
        try:
            contract = db.execute(select(Contract).where(Contract.charge_id == charge_id)).scalar()
            if not contract:
                logging.error(f"Webhhok Error: Contract  not found")
                return
            user = db.get(User, contract.buyer_id)
            contract.status = "DISPUTED"
            new_notification = Notification(
            conversation_id = get_conversation(db, contract.seller_id, contract.buyer_id),
            message = f"The payment of the following contract {contract.contract_id} is in dispute",
            sender_id = user.user_id)
            db.add(new_notification)
            db.commit()
            db.refresh(new_notification)
            background.add_task(send_notification, new_notification)
        except Exception as e:
            logging.error(f"error while procesing dispute {e}")
