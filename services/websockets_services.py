from models.notification import Notification
from models.conversation import Conversation
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select, or_, and_
from ws.manager import manager
from database.connection import engine
from models.contract import Contract

LocalSession = sessionmaker(autoflush=False, autocommit= False, bind=engine)

def get_conversation(db: Session, user_a: str, user_b: str):
    exists = db.execute(select(Conversation.conversation_id).where(
        or_(
            and_(Conversation.user_id_a == user_a, Conversation.user_id_b == user_b),
            and_(Conversation.user_id_a == user_b, Conversation.user_id_b == user_a)
        ))).scalar_one_or_none()
    if exists:
        return exists
    new_conversation = Conversation(
        user_id_a = user_a,
        user_id_b = user_b
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)

    return new_conversation.conversation_id

def verify_conversation(db: Session, user_a: str,  user_b: str):
    check = db.execute(select(Conversation.conversation_id).where(or_(
           and_(Conversation.user_id_a == user_a, Conversation.user_id_b == user_b),
            and_(Conversation.user_id_a == user_b, Conversation.user_id_b == user_a)
    ))).scalar_one_or_none()
    if not check:
        return False
    return check

async def send_notification(notification: Notification):

    await manager.send_message(notification.conversation_id, notification)


def save_message(db: Session, conversation_id: str, message: str, sender_id: str):
    new_notification = Notification(
        sender_id = sender_id,
        message = message,
        conversation_id = conversation_id
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification

def pending_notifications(db: Session, conversation_id: str, current_user_id: str):
    pending_messages = db.execute(select(Notification).where(Notification.conversation_id == conversation_id, Notification.is_read == False, Notification.sender_id != current_user_id)).scalars().all()
    return pending_messages

def mark_as_read(notification_id):
    with LocalSession() as db:
        notification = db.get(Notification, notification_id)
        notification.is_read = True
