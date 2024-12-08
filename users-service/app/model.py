from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Text, DECIMAL, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from uuid import UUID

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    user_id = Column(UUID, primary_key=True, index=True)
    user_name = Column(String(50), nullable=False)
    hashed_password = Column(Text, nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now().replace(tzinfo=None))
    role = Column(String(50), unique=True, nullable=False)
    verified = Column(Boolean, nullable=False)

    profile = relationship("User_profile", back_populates="Users")

class User_profiles:
    __tablename__ = 'user_profile'
    user_id = Column(UUID, ForeignKey('users.user_id'))
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20))
    address = Column(String(100))

    user = relationship("Users", back_populates = "user_profiles")


