from _operator import or_

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, logger
from model  import Base, Users, User_profiles
from schemas import UserCreate, UserOut, Token, UserUpdate
from database import engine, get_db
from services import create_access_token, verify_password
from sqlalchemy import update
from contextlib import asynccontextmanager
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
from uuid import UUID
from services import process_user_validation_request
import asyncio
from services import get_user_by_user_name
from services import create_user as create_new_user
from services import create_access_token
from services import update_user_data
import logging

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при запуске приложения
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Приложение будет работать в этом месте

    # Действия при завершении приложения
    await engine.dispose()

# Создание приложения
app = FastAPI(lifespan=lifespan)

@app.on_event("startup")
async def startup_event():
    db = await get_db().__anext__()
    app.state.task = asyncio.create_task(process_user_validation_request(db))

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_user_name(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя  или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users", response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Проверяем существующего пользователя по email или имени пользователя
        existing_user_query = select(Users).where(
            or_(Users.email == user.email, Users.user_name == user.user_name)
        )
        existing_user = await db.execute(existing_user_query)

        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="User with this email or username already exists"
            )

        # Создаем нового пользователя и профиль
        new_user = await create_new_user(db, user)

        # Загружаем данные пользователя с профилем
        result = await db.execute(
            select(Users)
            .options(selectinload(Users.profile))  # Подгружаем профиль
            .where(Users.user_id == new_user.user_id)
        )
        full_user = result.scalars().first()

        # Проверяем, что профиль загрузился корректно
        if not full_user or not full_user.profile:
            raise HTTPException(status_code=500, detail="Profile data not found")

        # Возвращаем данные пользователя с профилем
        return {
            "user_id": full_user.user_id,
            "user_name": full_user.user_name,
            "address": full_user.profile.address,
            "first_name": full_user.profile.first_name,
            "last_name": full_user.profile.last_name,
            "email": full_user.email,
            "phone": full_user.profile.phone,
            "role": full_user.role,
            "created_at": full_user.created_at,
            "verified": full_user.verified,
        }

    except Exception as e:
        logger.error(f"Ошибка регистрации пользователя: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")


@app.put("/users/{user_id}", response_model=UserUpdate)
async def update_user(
    user_id: UUID,
    updates: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        updated_user = await update_user_data(db, user_id, updates)
        return updated_user
    except HTTPException as e:
        raise e
    except Exception as e:
        # Логирование ошибки
        logger.error(f"Ошибка обновления пользователя: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )