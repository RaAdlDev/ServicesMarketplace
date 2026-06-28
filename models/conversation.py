from models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey
import uuid

class Conversation(Base):
    __tablename__="conversation"
    conversation_id: Mapped[str] = mapped_column(primary_key=True, default= lambda: str(uuid.uuid4()))
    user_id_a: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    user_id_b: Mapped[str] = mapped_column(ForeignKey("users.user_id"))

    