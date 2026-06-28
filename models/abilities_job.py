from sqlalchemy import Column, Table, ForeignKey, String
from models.base import Base


abilities_job = Table(
    "abilities_job",
    Base.metadata,
    Column("job_id", String, ForeignKey("job.job_id"), primary_key=True),
    Column("abilitie_id", String, ForeignKey("abilitie.abilitie_id"), primary_key=True)
        )