from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str = Field(..., max_length=100)  # Ограничение длины имени
    description: Optional[str] = None
    price: float = Field(..., ge=0)  # Цена должна быть >= 0
    stock: int = Field(..., ge=0)  # Количество должно быть >= 0

class ProductCreate(ProductBase):
    seller_id: UUID
    category_id: UUID

class ProductOut(ProductBase):
    product_id: UUID
    seller_id: UUID
    category_id: UUID

    class Config:
        orm_mode = True  # Позволяет работать с данными SQLAlchemy

class CategoryOut(BaseModel):
    category_id: UUID
    name: str
