from models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import func, ForeignKey
import uuid
from datetime import datetime


class Notification(Base):
    __tablename__="notification"
    notification_id: Mapped[str] = mapped_column(primary_key=True, default= lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    message: Mapped[str]
    is_read: Mapped[bool] = mapped_column(default=False)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversation.conversation_id"))