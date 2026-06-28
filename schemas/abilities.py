from pydantic import BaseModel, ConfigDict


class AbilitiesInput(BaseModel):
    name: str


class AbilitiesResponse(BaseModel):
    name: str
    abilitie_id: str

    model_config = ConfigDict(from_attributes=True)