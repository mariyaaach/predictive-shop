from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional
from enum import Enum
from datetime import datetime

# Определение возможных ролей пользователя
class UserRole(str, Enum):
    CONSUMER = "consumer"
    SELLER = "seller"
    ADMIN = "admin"

# Схема для базовой информации о пользователе
class UserBase(BaseModel):
    user_name: str
    email: EmailStr
    role: UserRole

# Схема для создания нового пользователя
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=64)

# Схема для отображения информации о пользователе (например, в ответах API)
class UserOut(UserBase):
    user_id: UUID
    verified: bool
    created_at: datetime

    class Config:
        orm_mode = True  # Указывает Pydantic, что данные будут приходить из SQLAlchemy-моделей

# Схема для базовой информации о профиле пользователя
class UserProfileBase(BaseModel):
    first_name: str
    last_name: str
    address: Optional[str]
    phone: Optional[str]

# Схема для обновления профиля пользователя
class UserProfileUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    address: Optional[str]
    phone: Optional[str]

# Схема для отображения профиля пользователя
class UserProfileOut(UserProfileBase):
    class Config:
        orm_mode = True

# Схема для отображения пользователя с его профилем
class UserWithProfile(UserOut):
    profile: Optional[UserProfileOut]
