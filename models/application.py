from models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, func, Enum
from typing import  Optional, Literal
import uuid
from datetime import datetime


class Application(Base):
    __tablename__= "application"
    application_id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    abilities_description: Mapped[str]
    job_id: Mapped[str] = mapped_column(ForeignKey("job.job_id"))
    professional_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    cv: Mapped[Optional[str]] = mapped_column(nullable=True)
    proposal: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    status: Mapped[Literal["PENDING", "ACEPTED", "REJECTED"]] = mapped_column(
        Enum("PENDING", "ACEPTED", "REJECTED", name= "application_status"), default= "PENDING"
    )

    professional: Mapped["User"] = relationship(back_populates="applications", foreign_keys=professional_id)
    job: Mapped["Job"] = relationship(back_populates="applications", foreign_keys=job_id)
    