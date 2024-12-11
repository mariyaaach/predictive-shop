from sqlalchemy import Column, String, Text, DECIMAL, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    user_id = Column(UUID, primary_key=True, index=True)
    user_name = Column(String(50), nullable=False, unique=True)
    hashed_password = Column(Text, nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    role = Column(String(50), nullable=False)
    verified = Column(Boolean, nullable=False, default=False)

    # Связь с профилем
    profile: Optional["User_profiles"] = relationship("User_profiles", back_populates="user", uselist=False)


class User_profiles(Base):
    __tablename__ = 'user_profiles'
    user_id = Column(UUID, ForeignKey('users.user_id'), primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(String(100), nullable=True)

    # Обратная связь с пользователем
    user = relationship("Users", back_populates="profile")
