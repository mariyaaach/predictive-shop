from confluent_kafka import Producer, Consumer

# Kafka Producer
producer = Producer({'bootstrap.servers': 'kafka:9093'})

# Отправка сообщения в Kafka
producer.produce('my_topic', key='key', value='value')
producer.flush()

# Kafka Consumer
consumer = Consumer({
    'bootstrap.servers': 'kafka:9093',
    'group.id': 'my_consumer_group',
    'auto.offset.reset': 'earliest'
})

consumer.subscribe(['my_topic'])
msg = consumer.poll(1.0)
if msg is not None:
    print(msg.value().decode('utf-8'))


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status, Depends
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import timedelta, datetime, timezone
from fastapi.security import OAuth2PasswordRequestForm

from uuid import uuid4
from .model import User
from .schemas import UserCreate, UserOut
from .database import get_db
from typing import Optional

# Настройки для токенов
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Настройка контекста для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Функция для хэширования паролей
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Функция для проверки пароля
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Создание токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    to_encode["sub"] = str(data["sub"])
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None



# Регистрация пользователя
async def register_user(user: UserCreate, db: AsyncSession):
    # Проверка на уникальность
    existing_user = await db.execute(
        select(User).where((User.email == user.email) | (User.user_name == user.user_name))
    )
    if existing_user.scalar():
        raise HTTPException(status_code=400, detail="User with this email or username already exists.")

    hashed_password = hash_password(user.password)
    new_user = User(
        user_id=uuid4(),
        user_name=user.user_name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        verified=False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


# Авторизация пользователя
async def login_user(form_data: OAuth2PasswordRequestForm, db: AsyncSession):
    result = await db.execute(select(User).where(User.user_name == form_data.username))
    user = result.scalar()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}


# Получение текущего пользователя
async def get_current_user(token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar()
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Инициализация
from sqlalchemy.ext.asyncio import AsyncSession
from .model import Base, User, UserProfile
from .database import engine

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
