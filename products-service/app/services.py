# product-service/app/services.py
import json
import asyncio
import os
from asyncio import Queue

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from model import Products, Categories  # Предполагается, что есть модели Products и Categories
from typing import Optional
from dotenv import load_dotenv
import logging
from schemas import ProductCreate, ProductUpdate

load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class KafkaService:
    def __init__(self):
        self.bootstrap_servers = 'kafka:9092'
        self.security_protocol = 'SASL_PLAINTEXT'
        self.sasl_mechanism = 'PLAIN'
        self.sasl_username = 'admin'
        self.sasl_password = 'admin-secret'
        self.group_id = 'product_service_group'
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        # Другие параметры
        self.validation_responses = Queue()  # Очередь для хранения ответов

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
            'user_service_response',  # Топик для ответов от User Service
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
                logger.info(f"Получено сообщение: {msg.value.decode('utf-8')}")
                data = json.loads(msg.value.decode('utf-8'))
                valid = data.get("valid")
                user_name = data.get("user_name")
                user_id = data.get("correlation_id")
                if valid is not None and user_name is not None:
                    await self.validation_responses.put({"user_id": user_id, "valid": valid, "user_name": user_name})
                    logger.info(f"Валидация успешна: user_name={user_name}, valid={valid}")
                else:
                    logger.warning("Некорректное сообщение.")
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")

    async def validate_user(self, user_id: int) -> Optional[dict]:
        message = {
            "user_id": user_id
        }

        try:
            await self.producer.send_and_wait(
                'user_service_request',
                key=str(user_id).encode('utf-8'),
                value=json.dumps(message).encode('utf-8')
            )
            logger.info(f"Sent user_service_request for user_id: {user_id}")
            # Ждем ответа из очереди
            while True:
                response = await self.validation_responses.get()
                if response.get("user_id") == user_id:
                    return response
        except Exception as e:
            logger.error(f"Failed to send user_service_request for user_id {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate user.")

async def create_product(db: AsyncSession, product_data: ProductCreate, seller_name: str) -> Products:
    """
    Создает продукт после проверки пользователя с ролью `seller` через Kafka.

    Args:
        db (AsyncSession): Сессия базы данных.
        product_data (ProductCreate): Данные для создания продукта.
        seller_name (str): Имя пользователя-продавца.

    Returns:
        Products: Созданный объект продукта.

    Raises:
        HTTPException: Если проверка продавца не удалась или категория недействительна.
    """
    # Проверяем существование category_id
    result = await db.execute(
        select(Categories).where(Categories.category_id == product_data.category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category_id"
        )

    # Создание продукта
    new_product = Products(
        seller_id=product_data.seller_id,
        seller_name=seller_name,  # Устанавливаем seller_name
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=product_data.stock,
        category_id=product_data.category_id
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

async def update_product(db: AsyncSession, product_id: int, product_data: ProductUpdate) -> Products:
    """
    Обновляет существующий продукт.

    Args:
        db (AsyncSession): Сессия базы данных.
        product_id (int): ID продукта для обновления.
        product_data (ProductUpdate): Данные для обновления продукта.

    Returns:
        Products: Обновленный объект продукта.

    Raises:
        HTTPException: Если продукт не найден или категория недействительна.
    """
    # Проверяем существование продукта
    result = await db.execute(
        select(Products).where(Products.product_id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Если обновляется category_id, проверяем существование новой категории
    if product_data.category_id is not None:
        result = await db.execute(
            select(Categories).where(Categories.category_id == product_data.category_id)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category_id"
            )

    # Обновляем поля продукта
    update_data = product_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

async def send_product_registration_message(product_id: int):
    """
    Отправляет сообщение в топик product.registration при регистрации нового продукта.

    Args:
        product_id (int): Идентификатор продукта.
    """
    message = {
        "product_id": product_id,
        "status": "registered"
    }
    try:
        await kafka_service.producer.send_and_wait(
            'product.registration',
            key=str(product_id).encode('utf-8'),
            value=json.dumps(message).encode('utf-8')
        )
        logger.info(f"Sent product.registration message for product_id: {product_id}")
    except Exception as e:
        logger.error(f"Failed to send product.registration message for product_id {product_id}: {e}")

kafka_service = KafkaService()