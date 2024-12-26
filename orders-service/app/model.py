# app/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    creation_time = Column(TIMESTAMP(timezone=True), server_default=func.now())
    total_price = Column(DECIMAL, nullable=False, default=0)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "orders_items"

    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(DECIMAL, nullable=False)
    price = Column(DECIMAL, nullable=False)
    seller_id = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")


class CartItem(Base):
    __tablename__ = "cart"

    cart_item_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String, nullable=False)
    price = Column(DECIMAL, nullable=False)
    seller_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
