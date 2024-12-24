import uuid
from typing import Optional

from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, DECIMAL, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID  # Использование UUID для PostgreSQL
from datetime import datetime

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Связь с профилем
    profile: Mapped[Optional["User_profiles"]] = relationship("User_profiles", back_populates="user", uselist=False)


class User_profiles(Base):
    __tablename__ = 'user_profiles'

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id'), primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Обратная связь с пользователем
    user: Mapped["Users"] = relationship("Users", back_populates="profile")
