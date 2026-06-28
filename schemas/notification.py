from pydantic import BaseModel, ConfigDict


class NotificationRsponse(BaseModel):
    created_at: str
    sender_id: str
    message: str

    model_config = ConfigDict(from_attributes=True)