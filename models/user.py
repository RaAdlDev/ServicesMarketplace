from models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Enum, func
from typing import Literal, List, Optional
import uuid
from datetime import datetime

class User(Base):
    __tablename__="users"
    user_id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(String(30), unique=True)
    role: Mapped[Literal["ADMIN", "CLIENT", "PROFESSIONAL"]] = mapped_column(Enum(
        "ADMIN", "CLIENT", "PROFESSIONAL", name= "role_types"
    ))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    is_active: Mapped[bool] = mapped_column(default=True)
    hashed_password: Mapped[str]
    stripe_connect_id: Mapped[Optional[str]] = mapped_column(nullable=True)


    profile: Mapped["Profile"] = relationship(back_populates="user")
    sold_contracts: Mapped[List["Contract"]] = relationship("Contract", back_populates="seller", foreign_keys="[Contract.seller_id]")
    bought_contracts: Mapped[List["Contract"]] = relationship("Contract", back_populates="buyer", foreign_keys="[Contract.buyer_id]")
    jobs: Mapped[List["Job"]] = relationship(back_populates="client")
    applications: Mapped[List["Application"]] = relationship(back_populates="professional")