# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from starlette.responses import JSONResponse

from model import Base, Order
from schemas import (
    OrderItemResponse, OrderCreate, OrderUpdateStatus, OrderResponse,
    CartTotalResponse, CartItemResponse, CartItemCreate
)
from services import (
    create_order as order_create,
    get_order,
    update_order_status as update_order,
    delete_order,
    add_to_cart,
    remove_from_cart,
    get_orders_by_user, get_cart_items, calculate_cart_total, kafka_service
)
from database import engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
from typing import List, Optional, Union
import asyncio
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация базы данных (создание таблиц, если необходимо)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created.")

    # Запуск KafkaService
    await kafka_service.start()
    logger.info("KafkaService started.")

    yield  # Приложение будет работать здесь

    # Остановка KafkaService
    await kafka_service.stop()
    logger.info("KafkaService stopped.")

    # Закрытие подключения к базе данных
    await engine.dispose()
    logger.info("Database connection closed.")

# Инициализация FastAPI с lifespan
app = FastAPI(lifespan=lifespan)

# Маршруты для заказов

@app.post("/orders/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    # Создание заказа
    created_order = await order_create(db, order)

    # Предзагрузка связанных данных
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .filter(Order.order_id == created_order.order_id)
    )
    result = await db.execute(query)
    loaded_order = result.scalar_one()

    # Преобразование в Pydantic-модель
    order_response = OrderResponse.model_validate(loaded_order)

    # Подготовка данных для Kafka
    order_dict = order_response.model_dump()
    await kafka_service.send_order_created(order_dict)

    return order_response

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def read_order(order_id: int, db: AsyncSession = Depends(get_db)):
    try:
        order = await get_order(db, order_id)
        order_response = OrderResponse.model_validate(order)
        return order_response
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Order not found")




@app.patch("/orders/{order_id}/status", response_model=Union[OrderResponse, dict])
async def update_order_status(order_id: int, status_update: OrderUpdateStatus, db: AsyncSession = Depends(get_db)):
    try:
        updated_order = await update_order(db, order_id, status_update.status)
        if updated_order is None:
            # Заказ был отменен и удален, отправляем сообщение в Kafka
            await kafka_service.send_order_canceled(order_id)
            return JSONResponse(
                content={"detail": "Order canceled and deleted"},
                status_code=status.HTTP_200_OK
            )
        order_response = OrderResponse.model_validate(updated_order)
        return order_response
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Order not found")

@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_endpoint(order_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await delete_order(db, order_id)
        # Отправка сообщения в Kafka об отмене заказа (опционально)
        await kafka_service.send_order_canceled(order_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Order not found")

# Маршруты для корзины

@app.post("/users/{user_id}/cart/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart_endpoint(
    user_id: int,
    item: CartItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Добавляет товар в корзину пользователя. Если товар уже есть, увеличивает количество.
    
    :param user_id: ID пользователя.
    :param item: Данные о товаре для добавления.
    :param db: Асинхронная сессия базы данных.
    :return: Добавленный или обновленный элемент корзины.
    """
    try:
        cart_item = await add_to_cart(db, user_id, item)
        cart_response = CartItemResponse.model_validate(cart_item)
        return cart_response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}/cart/{product_id}/", response_model=Optional[CartItemResponse], status_code=status.HTTP_200_OK)
async def remove_from_cart_endpoint(
    user_id: int,
    product_id: int,
    quantity: int = Query(1, ge=1, description="Количество для удаления"),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаляет указанное количество товара из корзины пользователя. Если количество достигает нуля, удаляет элемент полностью.
    
    :param user_id: ID пользователя.
    :param product_id: ID продукта для удаления.
    :param quantity: Количество для удаления.
    :param db: Асинхронная сессия базы данных.
    :return: Обновленный элемент корзины или сообщение об удалении.
    """
    try:
        cart_item = await remove_from_cart(db, user_id, product_id, quantity)
        if cart_item:
            cart_response = CartItemResponse.model_validate(cart_item)
            return cart_response
        else:
            return {"detail": "Cart item removed"}
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}/cart/", response_model=List[CartItemResponse])
async def get_user_cart_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Количество пропущенных записей для пагинации"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей для возврата")
):
    """
    Получает все позиции корзины пользователя.
    
    :param user_id: ID пользователя.
    :param db: Асинхронная сессия базы данных.
    :param skip: Количество пропущенных записей для пагинации.
    :param limit: Максимальное количество записей для возврата.
    :return: Список элементов корзины пользователя.
    """
    cart_items = await get_cart_items(db, user_id, skip=skip, limit=limit)
    if not cart_items:
        raise HTTPException(status_code=404, detail="Корзина пуста или пользователь не найден")
    return [CartItemResponse.model_validate(item) for item in cart_items]

@app.get("/users/{user_id}/cart/total/", response_model=CartTotalResponse)
async def get_cart_total_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Вычисляет итоговую цену корзины пользователя.
    
    :param user_id: ID пользователя.
    :param db: Асинхронная сессия базы данных.
    :return: Итоговая цена корзины.
    """
    total = await calculate_cart_total(db, user_id)
    return CartTotalResponse(user_id=user_id, total_price=float(total))


# Запуск приложения
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
