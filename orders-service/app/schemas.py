# app/schemas.py

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

ALLOWED_STATUSES = {"pending", "shipped", "delivered", "canceled"}

# Схемы для корзины
class CartItemCreate(BaseModel):
    product_id: int
    product_name: str
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    seller_id: int
    quantity: int = Field(default=1, ge=1)

    @field_validator('quantity')
    @classmethod
    def quantity_positive(cls, v):
        if v < 1:
            raise ValueError('quantity must be at least 1')
        return v

class CartItemResponse(BaseModel):
    cart_item_id: int
    user_id: int
    product_id: int
    product_name: str
    price: float
    seller_id: int
    quantity: int

    model_config = ConfigDict(from_attributes=True)

class CartTotalResponse(BaseModel):
    user_id: int
    total_price: float

    model_config = ConfigDict(from_attributes=True)

# Существующие схемы для заказов
class OrderItemCreate(BaseModel):
    product_id: int
    name: str
    quantity: int
    unit_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

    @field_validator('quantity')
    @classmethod
    def quantity_positive(cls, v):
        if v < 1:
            raise ValueError('quantity must be at least 1')
        return v

class OrderItemResponse(BaseModel):
    order_item_id: int
    product_id: int
    name: str
    quantity: int
    unit_price: float
    price: float

    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    order_id: int
    user_id: int
    status: str
    creation_time: datetime
    total_price: float
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)

class OrderUpdateStatus(BaseModel):
    status: str

    @field_validator('status')
    @classmethod
    def status_allowed(cls, v):
        if v not in ALLOWED_STATUSES:
            raise ValueError(f'status must be one of {ALLOWED_STATUSES}')
        return v
