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


from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update,  func
from . import model, schemas
from .model import Users
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

# Настройки для токенов
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Настройка контекста для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Функции для работы с паролями
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

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



async def get_user_by_email(db: AsyncSession, email: str) -> model.User:
    result = await db.execute(
        select(model.Users)
        .options(selectinload(model.Users.profile))
        .where(model.Users.email == email)
    )
    return result.scalar_one_or_none()

async def create_user(db:AsyncSession, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password) 
    db_user = model.Users(
        user_name=user.user_name,
        hashed_password=hashed_password,
        email=user.email,
        role=user.role,
        verified=user.verified,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    db_profile = model.User_profiles(
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            address=user.address
        )
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)

    return db_user


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(model.Users).where(model.Users.user_id == user_id))
    return result.scalars().first()


async def update_user_data(
    db: AsyncSession,
    user_id: UUID,
    updates: schemas.UserUpdate
) -> Users:
    
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

    # Сохраняем изменения
    await db.commit()
    await db.refresh(db_user)

    return db_user