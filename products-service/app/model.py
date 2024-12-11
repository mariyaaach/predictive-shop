from sqlalchemy import Column, String, Text, DECIMAL, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Optional

Base = declarative_base()

class Products(Base):
    __tablename__ = 'products'

    product_id = Column(UUID, primary_key=True, index=True)
    seller_id = Column(UUID, index=True, nullable=False)  # Не является primary_key
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(16, 2), default=0.00)
    stock = Column(Integer, nullable=False)
    category_id = Column(UUID, ForeignKey('categories.category_id'), nullable=False, index=True)  # Внешний ключ

    # Связь с категорией
    category = relationship("Categories", back_populates="products")


class Categories(Base):
    __tablename__ = 'categories'

    category_id = Column(UUID, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    # Связь с продуктами (одна категория -> много продуктов)
    products: List["Products"] = relationship("Products", back_populates="category", cascade="all, delete-orphan")
