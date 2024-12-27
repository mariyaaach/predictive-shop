# app/model.py
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(50), nullable=False, unique=True)
    hashed_password = Column(Text, nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String(50), nullable=False)
    verified = Column(Boolean, nullable=False, default=False)

    profile = relationship("User_profiles", back_populates="user", uselist=False)

class User_profiles(Base):
    __tablename__ = 'user_profiles'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(String(100), nullable=True)

    user = relationship("Users", back_populates="profile")
