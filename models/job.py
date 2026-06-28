from models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, func, ForeignKey
from typing import  Optional, List
import uuid
from datetime import datetime
from decimal import Decimal


class Job(Base):
    __tablename__="job"
    job_id: Mapped[str] = mapped_column(primary_key= True, default= lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    title: Mapped[str] = mapped_column(String(90))
    description: Mapped[str] 
    budget: Mapped[Decimal]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    requests: Mapped[Optional[int]] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    abilities: Mapped[List["Abilitie"]] = relationship(back_populates="jobs", secondary="abilities_job")
    client: Mapped["User"] = relationship(back_populates="jobs")
    applications: Mapped[List["Application"]] = relationship(back_populates="job")



