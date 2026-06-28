from models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, Enum, func
from typing import Literal, Optional
import uuid
from datetime import datetime
from decimal import Decimal


class Contract(Base):
    __tablename__="contract"
    contract_id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(ForeignKey("job.job_id"))
    seller_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    status: Mapped[Literal["PENDING_PAYMENT", "GUARANTEED", "COMPLETED", "REFUNDED", "FAILED", "DISPUTED"]] = mapped_column(
        Enum("PENDING_PAYMENT", "GUARANTEED", "COMPLETED","REFUNDED", "FAILED", "DISPUTED", name="contract_types"), default="PENDING_PAYMENT"
    )
    amount: Mapped[Decimal]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    payment_intent_id: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)
    transfer_id: Mapped[Optional[str]] = mapped_column(unique= True, nullable=True)
    refund_id: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)
    detail: Mapped[str]
    charge_id: Mapped[Optional[str]] = mapped_column(unique=True, nullable= True)


    seller: Mapped["User"] = relationship(back_populates= "sold_contracts", foreign_keys=[seller_id])
    buyer: Mapped["User"] = relationship(back_populates="bought_contracts", foreign_keys=[buyer_id])