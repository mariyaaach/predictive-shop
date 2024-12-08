import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, logger
from . import model, services, schemas
from .model import Base, Users
from .schemas import UserCreate, UserOut, Token
from .database import engine, get_db
from .services import get_user_by_email, create_access_token, verify_password, get_current_user
from sqlalchemy import update
from contextlib import asynccontextmanager
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List

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
            "first_name": new_user.fist_name,
            "last_name": new_user.last_name,
            "email": new_user.email,
            "phone": new_user.phone,
            "role": new_user.role
        }
    except Exception as e:
        logger.error(f"Ошибка регистрации пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")   

