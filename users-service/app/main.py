# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
import uvicorn
import logging
from contextlib import asynccontextmanager

from database import engine, get_db
from model import Base, Users
from schemas import UserCreate, UserOut, Token, UserUpdate
from services import (
    create_access_token,
    verify_password,
    get_user_by_user_name,
    create_user as create_new_user,
    update_user_data,
    send_registration_message,
    kafka_service
)
from auth import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created.")

    await kafka_service.start()
    logger.info("KafkaService started.")
    yield
    await kafka_service.stop()
    logger.info("KafkaService stopped.")

    await engine.dispose()
    logger.info("Database connection closed.")

app = FastAPI(lifespan=lifespan)

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_user_name(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем, не существует ли уже пользователь
    existing_q = select(Users).where(or_(Users.email == user.email, Users.user_name == user.user_name))
    existing_user = (await db.execute(existing_q)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email or username already exists")

    # Создаем нового пользователя
    new_user = await create_new_user(db, user)

    # Повторно загружаем с профилем
    result = await db.execute(
        select(Users)
        .options(selectinload(Users.profile))
        .where(Users.user_id == new_user.user_id)
    )
    full_user = result.scalars().first()
    if not full_user or not full_user.profile:
        raise HTTPException(status_code=500, detail="Profile data not found")

    # Отправка Kafka-сообщения (опционально)
    await send_registration_message(full_user.user_id)

    return UserOut(
        user_id=full_user.user_id,
        user_name=full_user.user_name,
        email=full_user.email,
        role=full_user.role,
        verified=full_user.verified,
        created_at=full_user.created_at,
        first_name=full_user.profile.first_name,
        last_name=full_user.profile.last_name,
        phone=full_user.profile.phone,
        address=full_user.profile.address
    )

@app.get("/users/me", response_model=UserOut)
async def read_users_me(
    current_user: dict = Depends(get_current_user),  # это словарь из get_user_info
):
    # current_user уже содержит все необходимые поля (см. get_user_info)
    return UserOut(**current_user)

@app.put("/users/{user_id}", response_model=UserUpdate)
async def update_user_endpoint(
    user_id: int,
    updates: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    updated_data = await update_user_data(db, user_id, updates)
    return updated_data


