from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional
from enum import Enum
from datetime import datetime

# Роли пользователей
class UserRole(str, Enum):
    CONSUMER = "consumer"
    SELLER = "seller"
    ADMIN = "admin"

class UserBase(BaseModel):
    user_name: str
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    user_id: UUID
    verified: bool
    created_at: datetime

    class Config:
        orm_mode = True

class UserProfileBase(BaseModel):
    first_name: str
    last_name: str
    address: Optional[str]
    phone: Optional[str]

class UserProfileOut(UserProfileBase):
    class Config:
        orm_mode = True

class UserWithProfile(UserOut):
    profile: Optional[UserProfileOut]
