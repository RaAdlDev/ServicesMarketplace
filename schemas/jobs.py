from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class JobInput(BaseModel):
    title: str
    description: str
    budget: Decimal

class JobResponse(BaseModel):
    title: str
    client_id: str
    description: str
    budget: Decimal
    job_id: str
    created_at: datetime
    requests: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


    
class MetaJobs(BaseModel):
    total_pages: int
    total_items: int
    page_size: int
    current_page: int
    has_previous: bool
    has_next: bool

    model_config = ConfigDict(from_attributes=True)
    


class PaginationJob(BaseModel, Generic[T]):
    data: List[T]
    meta: MetaJobs

    model_config = ConfigDict(from_attributes=True)
      

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[Decimal] = None