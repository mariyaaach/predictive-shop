# app/model.py
from typing import List, Optional

from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, DECIMAL, ForeignKey
from datetime import datetime

Base = declarative_base()

class Categories(Base):
    __tablename__ = 'categories'

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Связь с продуктами (одна категория -> много продуктов)
    products: Mapped[List["Products"]] = relationship("Products", back_populates="category", cascade="all, delete-orphan")


class Products(Base):
    __tablename__ = 'products'

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    seller_name: Mapped[str] = mapped_column(String(50), nullable=False)  # Изменено с user_name на seller_name
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[DECIMAL(16, 2)] = mapped_column(DECIMAL(16, 2), default=0.00)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('categories.category_id'), nullable=False, index=True)

    # Связь с категорией
    category: Mapped["Categories"] = relationship("Categories", back_populates="products")
