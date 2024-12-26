# app/services.py
import asyncio
import json
import logging
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from sqlalchemy.orm import selectinload

from database import get_db
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.bootstrap_servers = 'kafka:9092'
        self.security_protocol = 'SASL_PLAINTEXT'
        self.sasl_mechanism = 'PLAIN'
        self.sasl_username = 'admin'
        self.sasl_password = 'admin-secret'
        self.group_id = 'order_service_group'
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



        # Пример инициализации консьюмера
        self.consumer = AIOKafkaConsumer(
            'order_events_response',  # Укажите нужные топики, если требуется
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            security_protocol=self.security_protocol,
            sasl_mechanism=self.sasl_mechanism,
            sasl_plain_username=self.sasl_username,
            sasl_plain_password=self.sasl_password

        )
        await self.consumer.start()
        logger.info("Kafka consumer started.")

        # Запуск задачи для обработки сообщений (если необходимо)
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
                # Обработка сообщений из Kafka, связанных с заказами
                data = json.loads(msg.value.decode('utf-8'))
                event = data.get("event")
                if event == "order_processed":
                    await self.handle_order_processed(data.get("data"))
                # Добавьте обработку других событий по мере необходимости
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")

    async def handle_order_processed(self, data: dict):
        # Реализуйте логику обработки события обработки заказа, если необходимо
        logger.info(f"Handled order_processed event: {data}")

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

    try:
        # Группируем продукты по product_id для объединения количеств
        product_map = {}
        for item in order.items:
            if item.product_id in product_map:
                logger.info(item.product_id)
                logger.info(item.quantity)
                logger.info(item.unit_price)
                product_map[item.product_id]['quantity'] += item.quantity
                product_map[item.product_id]['price'] += item.quantity * item.unit_price
            else:
                product_map[item.product_id] = {
                    'product_id': item.product_id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'price': item.quantity * item.unit_price,
                    'seller_id': item.seller_id
                }

        # Подготовка данных для вставки в таблицу orders_items
        order_items = []
        total_price = Decimal('0.00')
        for product in product_map.values():
            order_item = OrderItem(
                product_id=product['product_id'],
                name=product['name'],
                quantity=product['quantity'],
                unit_price=product['unit_price'],
                price=product['price'],
                seller_id=product['seller_id']
            )
            order_items.append(order_item)
            total_price += product['price']
            logger.info(total_price)
            for i in order_items:
                logger.info(i)

        # Создание нового заказа
        new_order = Order(
            user_id=order.user_id,
            status="pending",
            total_price=total_price,
            items=order_items  # Связываем позиции заказа с заказом
        )

        # Добавление заказа и позиций заказа в сессию
        db.add(new_order)

        # Одновременный коммит всех изменений
        await db.commit()

        # Обновление объекта заказа с данными из базы
        await db.refresh(new_order)

        logger.info(f"Created new order with order_id: {new_order.order_id}")
        return new_order

    except Exception as e:
        logger.error(f"Error creating order: {e}")
        await db.rollback()
        raise

async def get_order(db: AsyncSession, order_id: int) -> Order:
    """Получить заказ с предзагрузкой связанных товаров."""
    query = (
    select(Order)
    .options(selectinload(Order.items))  # Предзагрузка связанных товаров
    .filter(Order.order_id == order_id)
        )
    result = await db.execute(query)
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
    """Удаляет заказ и связанные с ним товары."""
    # Сначала удаляем все товары, связанные с заказом
    delete_items_stmt = delete(OrderItem).where(OrderItem.order_id == order_id)
    await db.execute(delete_items_stmt)

    # Теперь удаляем сам заказ
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