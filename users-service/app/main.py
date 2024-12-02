from fastapi import FastAPI, Depends
from .services import register_user, login_user, get_current_user
from .schemas import UserCreate, UserOut
from .database import init_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

app = FastAPI()


# Настройка авторизации через OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# Регистрация пользователя
@app.post("/register/", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await register_user(user, db)


# Авторизация пользователя
@app.post("/login/")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    return await login_user(form_data, db)


# Получение данных текущего пользователя
@app.get("/users/me/", response_model=UserOut)
async def read_users_me(current_user: UserOut = Depends(get_current_user)):
    return current_user


# Функция для инициализации базы данных при старте приложения
@app.on_event("startup")
async def on_startup():
    await init_db()
