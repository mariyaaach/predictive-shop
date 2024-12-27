# product-service/app/main.py
from sqlalchemy.orm import selectinload
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from model import Products, Categories, Base
from schemas import ProductOut, ProductCreate, ProductUpdate, CategoryOut
from database import get_db, engine
from services import create_product, update_product, KafkaService, send_product_registration_message
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
import logging
import json
from services import kafka_service
from typing import List

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация базы данных
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

# Создание приложения
app = FastAPI(lifespan=lifespan)

@app.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(
        product: ProductCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    Создает новый продукт после проверки пользователя с ролью `seller`.
    """
    try:
        # Валидация пользователя через Kafka
        seller =  await kafka_service.validate_user(product.seller_id)
        logger.info("После валидации создаем заказ для " + seller.get('user_name'))

        seller_name = seller.get('user_name')  # Изменено на seller_name

        # Создаем новый продукт с seller_name
        logger.info(product)
        new_product = await create_product(db, product, seller_name)
        logger.info(f"Создан новый продукт: {new_product.product_id}")

        # Отправляем сообщение в Kafka о регистрации
        await send_product_registration_message(new_product.product_id)

        return new_product
    except HTTPException as e:
        logger.error(f"HTTPException при создании продукта: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Ошибка регистрации продукта: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при создании продукта")

@app.patch("/products/{product_id}", response_model=ProductOut)
async def update_product_endpoint(
        product_id: int,
        product_update: ProductUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    Обновляет существующий продукт.
    """
    try:
        updated_product = await update_product(db, product_id, product_update)
        logger.info(f"Обновлен продукт: {updated_product.product_id}")
        return updated_product
    except HTTPException as e:
        logger.error(f"HTTPException при обновлении продукта: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Ошибка обновления продукта: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

@app.get("/products/{product_id}", response_model=ProductOut)
async def get_product_endpoint(
        product_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Получает информацию о продукте по его ID.
    """
    try:
        result = await db.execute(
            select(Products).where(Products.product_id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return product
    except HTTPException as e:
        logger.error(f"HTTPException при получении продукта: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Ошибка получения продукта: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

@app.get("/products", response_model=list[ProductOut])
async def get_all_products_endpoint(
        db: AsyncSession = Depends(get_db)
):
    """
    Получает список всех продуктов.
    """
    try:
        result = await db.execute(select(Products))
        products = result.scalars().all()
        return products
    except Exception as e:
        logger.error(f"Ошибка получения всех продуктов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
@app.get("/products/seller/{seller_id}", response_model=list[ProductOut])
async def get_products_by_seller_endpoint(
        seller_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Получает список продуктов по ID продавца.
    """
    try:
        result = await db.execute(
            select(Products).where(Products.seller_id == seller_id)
        )
        products = result.scalars().all()
        return products
    except Exception as e:
        logger.error(f"Ошибка получения продуктов для seller_id {seller_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
    
@app.get("/categories", response_model=List[CategoryOut])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """
    Возвращаем список всех категорий (category_id, name) из таблицы.
    """
    result = await db.execute(select(Categories))
    categories = result.scalars().all()
    return categories

@app.get("/categories/{category_id}", response_model=CategoryOut)
async def get_category_by_id(category_id: int, db: AsyncSession = Depends(get_db)):
    """
    Возвращает одну категорию по ее ID.
    """
    result = await db.execute(select(Categories).where(Categories.category_id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category
