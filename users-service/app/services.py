# user-service/app/services.py
import asyncio
import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from model import Users
from fastapi import HTTPException, status
import logging
from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.bootstrap_servers = 'kafka:9092'
        self.security_protocol = 'SASL_PLAINTEXT'
        self.sasl_mechanism = 'PLAIN'
        self.sasl_username = 'admin'
        self.sasl_password = 'admin-secret'
        self.group_id = 'user_service_group'
        self.producer: AIOKafkaProducer = None
        self.consumer: AIOKafkaConsumer = None

    async def start(self):
        # Инициализация продюсера
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            security_protocol=self.security_protocol,
            sasl_mechanism=self.sasl_mechanism,
            sasl_plain_username=self.sasl_username,
            sasl_plain_password=self.sasl_password
        )
        await self.producer.start()
        logger.info("Kafka producer started.")

        # Инициализация консьюмера
        self.consumer = AIOKafkaConsumer(
            'user_service_request',
            'user.verified',
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            security_protocol=self.security_protocol,
            sasl_mechanism=self.sasl_mechanism,
            sasl_plain_username=self.sasl_username,
            sasl_plain_password=self.sasl_password
        )
        await self.consumer.start()
        logger.info("Kafka consumer started.")

        # Запуск задачи для обработки сообщений
        asyncio.create_task(self.consume_messages())

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped.")
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped.")

    async def consume_messages(self):
        try:
            async for msg in self.consumer:
                if msg.topic == 'user_service_request':
                    logger.info("Пришло сообщение в топик u s")
                    await asyncio.create_task(self.handle_user_validation(msg))
                elif msg.topic == 'user.verified':
                    await asyncio.create_task(self.handle_user_verified(msg))
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")

    async def handle_user_validation(self, msg):
        data = json.loads(msg.value.decode('utf-8'))
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        if not user_id:
            logger.warning("Received user_service_request without user_id.")
            return

        # Получаем сессию базы данных
        async for db in get_db():
            break  # Берем первую доступную сессию

        try:
            result = await db.execute(
                select(Users).where(Users.user_id == user_id, Users.role == 'seller')
            )
            user = result.scalar_one_or_none()

            response = {"user_id": user_id, "valid": bool(user), "user_name": user.user_name, "correlation_id" : user_id}
            try:
                await self.producer.send_and_wait(
                    'user_service_response',
                    key=str(user_id).encode('utf-8'),
                    value=json.dumps(response).encode('utf-8')
                )
                logger.info(f"Sent user_service_response for user_id: {user_id}")
            except Exception as e:
                logger.error(f"Failed to send user_service_response for user_id {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing user_service_request for user_id {user_id}: {e}")

    async def handle_user_verified(self, msg):
        data = json.loads(msg.value.decode('utf-8'))
        user_id = data.get("user_id")
        if not user_id:
            logger.warning("Received user.verified message without user_id.")
            return

        # Получаем сессию базы данных
        async for db in get_db():
            break  # Берем первую доступную сессию

        try:
            result = await db.execute(
                select(Users).where(Users.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {user_id} not found for verification.")
                return

            user.verified = True
            await db.commit()
            logger.info(f"User {user_id} verified and status updated in the database.")
        except Exception as e:
            logger.error(f"Error updating user verification status for user_id {user_id}: {e}")
            await db.rollback()

async def send_registration_message(user_id: int):
    """
    Отправляет сообщение в топик user.registration при регистрации нового пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
    """
    message = {
        "user_id": user_id,
        "status": "registered"
    }
    try:
        await kafka_service.producer.send_and_wait(
            'user.registration',
            key=str(user_id).encode('utf-8'),
            value=json.dumps(message).encode('utf-8')
        )
        logger.info(f"Sent user.registration message for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to send user.registration message for user_id {user_id}: {e}")

# Инициализация KafkaService
kafka_service = KafkaService()




from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update,  func
from model import Users, User_profiles
from schemas import UserCreate, UserUpdate
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



def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

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

async def get_user_info(db: AsyncSession, user_id: int) -> Optional[dict]:
    """
    Возвращаем словарь с полями user + profile (если профиль есть).
    """
    # Загружаем пользователя с подгруженным profile
    result = await db.execute(
        select(Users)
        .options(selectinload(Users.profile))
        .where(Users.user_id == user_id)
    )
    db_user = result.scalars().first()

    if not db_user:
        return None

    profile = db_user.profile
    return {
        "user_id": db_user.user_id,
        "user_name": db_user.user_name,
        "email": db_user.email,
        "role": db_user.role,
        "created_at": db_user.created_at,
        "verified": db_user.verified,
        "first_name": profile.first_name if profile else "",
        "last_name": profile.last_name if profile else "",
        "phone": profile.phone if profile else "",
        "address": profile.address if profile else "",
    }

async def get_user_by_user_name(db: AsyncSession, user_name: str) -> Optional[Users]:
    q = select(Users).where(Users.user_name == user_name)
    result = await db.execute(q)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data):
    """
    Создаём запись в таблице Users + связанную запись в user_profiles.
    """
    hashed_password = get_password_hash(user_data.password)
    db_user = Users(
        user_name=user_data.user_name,
        hashed_password=hashed_password,
        email=user_data.email,
        role=user_data.role,
        verified=False
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # Создаём профиль
    db_profile = User_profiles(
        user_id=db_user.user_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        address=user_data.address
    )
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return db_user

async def update_user_data(db: AsyncSession, user_id: int, updates) -> dict:
    """
    Обновляем пользователя + профиль.
    Возвращаем словарь (для схемы UserUpdate).
    """
    result = await db.execute(
        select(Users)
        .options(selectinload(Users.profile))
        .where(Users.user_id == user_id)
    )
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Обновляем поля Users
    if updates.user_name is not None:
        db_user.user_name = updates.user_name
    if updates.email is not None:
        db_user.email = updates.email
    if updates.role is not None:
        db_user.role = updates.role
    if updates.verified is not None:
        db_user.verified = updates.verified

    # Обновляем профиль
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
    return {
        "user_name": db_user.user_name,
        "email": db_user.email,
        "role": db_user.role,
        "verified": db_user.verified,
        "first_name": db_user.profile.first_name,
        "last_name": db_user.profile.last_name,
        "phone": db_user.profile.phone,
        "address": db_user.profile.address,
    }
