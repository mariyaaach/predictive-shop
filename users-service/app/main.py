import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, logger
from model  import Base, Users, User_profiles
from schemas import UserCreate, UserOut, Token, UserUpdate
from database import engine, get_db
from services import get_user_by_email, create_access_token, verify_password
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
    try:
        updated_user = await services.update_user_data(db, user_id, updates)
        return updated_user
    except HTTPException as e:
        raise e
    except Exception as e:
        # Логирование ошибки
        print(f"Ошибка при обновлении пользователя: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )