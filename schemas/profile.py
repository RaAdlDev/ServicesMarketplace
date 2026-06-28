from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from schemas.abilities import AbilitiesResponse


class ProfileResponse(BaseModel):
    description: Optional[str] = None
    social_media: Optional[str] = None
    abilities: Optional[List[AbilitiesResponse]] = None
    experience: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    description: Optional[str] = None
    social_media: Optional[str] = None
    abilities: Optional[List[str]] = None
    experience: Optional[str] = None