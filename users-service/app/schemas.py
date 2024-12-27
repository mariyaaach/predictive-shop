# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Токены
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

# Базовая модель пользователя (все поля, которые храним в таблице user + профиль)
class UserBase(BaseModel):
    user_name: str
    email: EmailStr
    role: str
    verified: bool

# Модель для создания пользователя
class UserCreate(UserBase):
    password: str
    first_name: str
    last_name: str
    phone: str
    address: str

# Модель для ответа (UserOut) – выводим ВСЕ поля
class UserOut(BaseModel):
    user_id: int
    user_name: str
    email: EmailStr
    role: str
    verified: bool
    created_at: datetime
    first_name: str
    last_name: str
    phone: str
    address: str

    class Config:
        from_attributes = True  # Позволяет Pydantic считывать данные из SQLAlchemy-моделей

# Модель для обновления
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
        orm_mode = True
