from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional
from enum import Enum
from datetime import datetime


# Схемы для аутентификации
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None


# Схема для базовой информации о пользователе
class UserBase(BaseModel):
    user_id: UUID
    user_name: str
    email: EmailStr
    role: str
    first_name: str
    last_name: str
    phone: str
    address: str
    verified: bool


# Схема для создания нового пользователя
class UserCreate(UserBase):
    password: str 

# Схема для отображения информации о пользователе (например, в ответах API)
class UserOut(UserBase):
    verified: bool
    created_at: datetime

    class Config:
        orm_mode = True  # Указывает Pydantic, что данные будут приходить из SQLAlchemy-моделей


