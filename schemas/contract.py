from pydantic import BaseModel, ConfigDict
from typing import Literal
from decimal import Decimal
from datetime import datetime

class ContractResponse(BaseModel):
    job_id: str
    seller_id: str
    buyer_id: str
    status: Literal["PENDING_PAYMENT", "GUARANTEED", "COMPLETED", "REFUNDED", "FAILED", "DISPUTED"]
    amount: Decimal
    created_at: datetime
    updated_at: datetime
    detail: str
    
    model_config = ConfigDict(from_attributes=True)

