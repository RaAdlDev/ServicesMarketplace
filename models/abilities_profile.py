from sqlalchemy import Column, Table, ForeignKey, String
from models.base import Base


abilities_profile = Table(
    "abilities_profile",
    Base.metadata,
    Column("profile_id", String, ForeignKey("profile.profile_id"), primary_key=True),
    Column("abilitie_id", String, ForeignKey("abilitie.abilitie_id"), primary_key=True)
        )