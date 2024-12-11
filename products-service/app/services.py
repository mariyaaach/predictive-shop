import json
from confluent_kafka import Producer, Consumer
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .model import Products
from .schemas import ProductCreate

# Kafka Producer для отправки запроса
producer = Producer({'bootstrap.servers': 'kafka:9093'})

# Kafka Consumer для получения ответа
consumer = Consumer({
    'bootstrap.servers': 'kafka:9093',
    'group.id': 'product_service_group',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe(['user_service_response'])

async def validate_seller(seller_id: UUID) -> bool:
    """
    Проверяет существование пользователя с ролью `seller` через Kafka.

    Args:
        seller_id (UUID): ID пользователя.

    Returns:
        bool: True, если пользователь найден и имеет роль `seller`.
    """
    # Отправляем сообщение в Kafka
    producer.produce('user_service_request', key=str(seller_id), value=json.dumps({"user_id": str(seller_id)}))
    producer.flush()

    # Ожидаем ответа из Kafka
    while True:
        msg = consumer.poll(5.0)  # Ждем до 5 секунд
        if msg is None:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Timeout while validating seller ID"
            )
        if msg.key().decode('utf-8') == str(seller_id):
            response = json.loads(msg.value().decode('utf-8'))
            return response.get("valid", False)

async def create_product(db: AsyncSession, product_data: ProductCreate) -> Products:
    """
    Создает продукт после проверки пользователя с ролью `seller` через Kafka.

    Args:
        db (AsyncSession): Сессия базы данных.
        product_data (ProductCreate): Данные для создания продукта.

    Returns:
        Products: Созданный объект продукта.

    Raises:
        HTTPException: Если проверка продавца не удалась.
    """
    # Проверяем пользователя через Kafka
    is_valid_seller = await validate_seller(product_data.seller_id)
    if not is_valid_seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid seller ID or user is not a seller"
        )

    # Создание продукта
    new_product = Products(
        product_id=UUID(),
        seller_id=product_data.seller_id,  # Это user_id из микросервиса пользователей
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
