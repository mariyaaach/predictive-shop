# app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class ProductBase(BaseModel):
    name: Optional[str] = Field(None, max_length=100)  # Ограничение длины имени
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)  # Цена должна быть >= 0
    stock: Optional[int] = Field(None, ge=0)  # Количество должно быть >= 0
    category_id: Optional[int] = None  # Идентификатор категории

class ProductCreate(ProductBase):
    seller_id: int
    category_id: int

class ProductUpdate(ProductBase):
    pass  # Наследуется от ProductBase без изменений

class ProductOut(ProductBase):
    product_id: int
    seller_id: int
    seller_name: str  # Изменено с user_name на seller_name
    category_id: int

    class Config:
        from_attributes = True  # Позволяет работать с данными SQLAlchemy

class CategoryOut(BaseModel):
    category_id: int
    name: str

    class Config:
        from_attributes = True
