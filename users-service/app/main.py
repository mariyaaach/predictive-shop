import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, logger
from . import model, services, schemas
from .model import Base, Users, User_profiles
from .schemas import UserCreate, UserOut, Token, UserUpdate
from .database import engine, get_db
from .services import get_user_by_email, create_access_token, verify_password, get_current_user
from sqlalchemy import update
from contextlib import asynccontextmanager
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
from uuid import UUID

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

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await services.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        existing_user = await db.execute(
            select(Users).where((Users.email == user.email))
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User with this email or phone already exists")
        
        new_user = await services.create_user(db, user)

        return {
            "user_id": new_user.user_id,
            "first_name": new_user.profile.fist_name,
            "last_name": new_user.profile.last_name,
            "email": new_user.email,
            "phone": new_user.profile.phone,
            "role": new_user.role
        }
    except Exception as e:
        logger.error(f"Ошибка регистрации пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")   

@app.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID, 
    updates: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Получаем пользователя вместе с профилем
    result = await db.execute(
        select(Users)
        .options(selectinload(Users.profile))
        .where(Users.user_id == user_id)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Если приходят данные для профиля, но профиль отсутствует, выбрасываем ошибку
    if any([updates.first_name, updates.last_name, updates.phone, updates.address]) and not db_user.profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile does not exist for this user"
        )

    # Обновляем поля пользователя
    if updates.user_name is not None:
        db_user.user_name = updates.user_name
    if updates.email is not None:
        db_user.email = updates.email
    if updates.role is not None:
        db_user.role = updates.role
    if updates.verified is not None:
        db_user.verified = updates.verified

    # Обновляем профиль, если он существует
    if db_user.profile:
        if updates.first_name is not None:
            db_user.profile.first_name = updates.first_name
        if updates.last_name is not None:
            db_user.profile.last_name = updates.last_name
        if updates.phone is not None:
            db_user.profile.phone = updates.phone
        if updates.address is not None:
            db_user.profile.address = updates.address

    await db.commit()
    await db.refresh(db_user)
    return db_user