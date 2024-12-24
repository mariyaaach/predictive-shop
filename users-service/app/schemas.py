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

# Схема для отображения информации о пользователе
class UserOut(UserBase):
    user_id: int
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Указывает Pydantic, что данные будут приходить из SQLAlchemy-моделей


class UserUpdate(BaseModel):
    user_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    verified: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfileOut(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str]
    address: Optional[str]

    class Config:
        from_attributes = True