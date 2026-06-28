from models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from typing import  List
import uuid

class Abilitie(Base):
    __tablename__="abilitie"
    abilitie_id: Mapped[str] = mapped_column(primary_key=True, default= lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(unique=True)

    profiles: Mapped[List["Profile"]] = relationship(back_populates="abilities", secondary="abilities_profile")
    jobs: Mapped[List["Job"]] = relationship(back_populates="abilities", secondary="abilities_job")