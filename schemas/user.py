from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Literal, Optional, TypeVar, Generic, List
from schemas.profile import ProfileResponse
import re
from datetime import datetime

T = TypeVar("T")

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Literal["CLIENT", "PROFESSIONAL"]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        if not re.search(r'[A-Z]', v):
            raise ValueError("password must have a capital letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("password must have a lowercase letter")
        if not re.search(r'[0-9]', v):
            raise ValueError("password must have a number")
        if not re.search(r'[@$!%*?&._-]', v):
            raise ValueError("password must have a special character")
        return v
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    username: str
    user_id: str
    email: EmailStr
    role: Literal["ADMIN", "CLIENT", "PROFESSIONAL"]
    profile: Optional[ProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
    

class Meta(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    page_size: int
    has_next: bool
    has_previous: bool

class Response(BaseModel, Generic[T]):
    data: List[T]
    meta: Meta


            
