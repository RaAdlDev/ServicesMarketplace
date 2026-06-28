from models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey
import uuid
from typing import Optional, List


class Profile(Base):
    __tablename__="profile"
    profile_id: Mapped[str] = mapped_column(primary_key=True, default= lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    social_media: Mapped[Optional[str]] = mapped_column(nullable=True)
    experience: Mapped[Optional[str]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="profile")
    abilities: Mapped[List["Abilitie"]] = relationship(back_populates="profiles", secondary="abilities_profile")