from pydantic import BaseModel, ConfigDict
from typing import Optional

class AplicationInput(BaseModel):
    abilities_description: str
    proposal: str
    cv: Optional[str] = None


class AplicationResponse(BaseModel):
    application_id: str
    abilities_description: str
    job_id: str
    proposal: str
    created_at: str
    cv: Optional[str] = None


    model_config = ConfigDict(from_attributes=True)

class ApplicationAcepted(BaseModel):
    message: str


