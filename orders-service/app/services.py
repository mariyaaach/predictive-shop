# app/services.py
import asyncio
import json
import logging
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from database import get_db
from model import Users  # Убедитесь, что модель Users определена
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.bootstrap_servers = 'kafka:9092'  # Используйте порт 9093 для SASL_PLAINTEXT, если необходимо
        self.security_protocol = 'SASL_PLAINTEXT'
        self.sasl_mechanism = 'PLAIN'
        self.sasl_username = 'admin'
        self.sasl_password = 'admin-secret'
        self.group_id = 'user_service_group'
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None

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
                    asyncio.create_task(self.handle_user_validation(msg))
                elif msg.topic == 'user.verified':
                    asyncio.create_task(self.handle_user_verified(msg))
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

            response = {"user_id": user_id, "valid": bool(user), "user_name": user_name}
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

    async def send_order_created(self, order_data: dict):
        """
        Отправляет сообщение о создании заказа в Kafka.
        
        Args:
            order_data (dict): Данные созданного заказа.
        """
        message = {
            "event": "order_created",
            "data": order_data
        }
        try:
            await self.producer.send_and_wait(
                'order_events',
                key=str(order_data['order_id']).encode('utf-8'),
                value=json.dumps(message).encode('utf-8')
            )
            logger.info(f"Sent order_created message for order_id: {order_data['order_id']}")
        except Exception as e:
            logger.error(f"Failed to send order_created message for order_id {order_data['order_id']}: {e}")

    async def send_order_canceled(self, order_id: int):
        """
        Отправляет сообщение об отмене заказа в Kafka.
        
        Args:
            order_id (int): ID отмененного заказа.
        """
        message = {
            "event": "order_canceled",
            "data": {
                "order_id": order_id
            }
        }
        try:
            await self.producer.send_and_wait(
                'order_events',
                key=str(order_id).encode('utf-8'),
                value=json.dumps(message).encode('utf-8')
            )
            logger.info(f"Sent order_canceled message for order_id: {order_id}")
        except Exception as e:
            logger.error(f"Failed to send order_canceled message for order_id {order_id}: {e}")

# Инициализация KafkaService
kafka_service = KafkaService()





from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from model import Order, OrderItem, CartItem
from schemas import OrderCreate, CartItemCreate
from sqlalchemy.exc import NoResultFound
from typing import Optional, List
from decimal import Decimal

async def create_order(db: AsyncSession, order: OrderCreate) -> Order:
    new_order = Order(
        user_id=order.user_id,
        status="pending",
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    total = Decimal('0.00')
    for item in order.items:
        # Проверяем, есть ли уже товар с таким product_id в заказе
        existing_item = None
        for existing in new_order.items:
            if existing.product_id == item.product_id:
                existing_item = existing
                break
        if existing_item:
            existing_item.quantity += item.quantity
            existing_item.price = existing_item.quantity * existing_item.unit_price
        else:
            order_item = OrderItem(
                order_id=new_order.order_id,
                product_id=item.product_id,
                name=item.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.quantity * item.unit_price
            )
            db.add(order_item)
            new_order.items.append(order_item)
        total += item.quantity * item.unit_price
    
    new_order.total_price = total
    await db.commit()
    await db.refresh(new_order)
    return new_order

async def get_order(db: AsyncSession, order_id: int) -> Order:
    result = await db.execute(
        select(Order)
        .where(Order.order_id == order_id)
        .options(Order.items)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NoResultFound(f"Order with id {order_id} not found")
    return order

async def update_order_status(db: AsyncSession, order_id: int, status: str) -> Optional[Order]:
    # Обновляем статус заказа
    stmt = update(Order).where(Order.order_id == order_id).values(status=status)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise NoResultFound(f"Order with id {order_id} not found")
    await db.commit()
    
    if status == "canceled":
        await delete_order(db, order_id)
        return None
    
    # Возвращаем обновленный заказ
    return await get_order(db, order_id)

async def delete_order(db: AsyncSession, order_id: int):
    stmt = delete(Order).where(Order.order_id == order_id)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise NoResultFound(f"Order with id {order_id} not found")
    await db.commit()


async def get_orders_by_user(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.creation_time.desc())
        .offset(skip)
        .limit(limit)
        .options(Order.items)
    )
    orders = result.scalars().all()
    return orders

async def add_to_cart(db: AsyncSession, user_id: int, item: CartItemCreate) -> CartItem:
    # Проверяем, существует ли уже товар в корзине пользователя
    stmt = select(CartItem).where(
        CartItem.user_id == user_id,
        CartItem.product_id == item.product_id
    )
    result = await db.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if cart_item:
        # Увеличиваем количество существующего товара
        cart_item.quantity += item.quantity
        await db.commit()
        await db.refresh(cart_item)
    else:
        # Создаем новый элемент корзины
        new_cart_item = CartItem(
            user_id=user_id,
            product_id=item.product_id,
            name=item.name,
            price=item.price,
            seller_id=item.seller_id,
            quantity=item.quantity
        )
        db.add(new_cart_item)
        await db.commit()
        await db.refresh(new_cart_item)
        cart_item = new_cart_item

    return cart_item

# Функция для удаления элемента из корзины (уменьшение количества или удаление)
async def remove_from_cart(db: AsyncSession, user_id: int, product_id: int, quantity: int = 1) -> Optional[CartItem]:
    # Ищем элемент в корзине
    stmt = select(CartItem).where(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id
    )
    result = await db.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise NoResultFound(f"Product with id {product_id} not found in user's cart")

    if cart_item.quantity > quantity:
        # Уменьшаем количество
        cart_item.quantity -= quantity
        await db.commit()
        await db.refresh(cart_item)
    elif cart_item.quantity == quantity:
        # Удаляем элемент из корзины
        await delete_cart_item(db, cart_item.cart_item_id)
        cart_item = None
    else:
        raise ValueError(f"Cannot remove {quantity} items as only {cart_item.quantity} are in the cart")

    return cart_item

# Функция для полного удаления элемента из корзины
async def delete_cart_item(db: AsyncSession, cart_item_id: int):
    stmt = delete(CartItem).where(CartItem.cart_item_id == cart_item_id)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise NoResultFound(f"Cart item with id {cart_item_id} not found")
    await db.commit()

# Функция для получения всех элементов корзины пользователя
async def get_cart_items(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[CartItem]:
    stmt = select(CartItem).where(CartItem.user_id == user_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    cart_items = result.scalars().all()
    return cart_items

# Функция для расчета итоговой цены корзины пользователя
async def calculate_cart_total(db: AsyncSession, user_id: int) -> Decimal:
    stmt = select(sum(CartItem.price * CartItem.quantity)).where(CartItem.user_id == user_id)
    result = await db.execute(stmt)
    total = result.scalar_one_or_none()
    return total or Decimal('0.00')