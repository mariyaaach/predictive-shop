# product-service/app/main.py
from sqlalchemy.orm import selectinload
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from model import Products, Categories, Base
from schemas import ProductOut, ProductCreate, ProductUpdate
from database import get_db, engine
from services import create_product, update_product, KafkaService, send_product_registration_message
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
import logging
import json

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Глобальный объект KafkaService
kafka_service: KafkaService | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация базы данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created.")
    global kafka_service
    kafka_service = KafkaService()

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
        validation_response = await kafka_service.validate_user(product.seller_id)
        if not validation_response["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a seller or does not exist."
            )
        seller_name = validation_response["seller_name"]  # Изменено на seller_name

        # Создаем новый продукт с seller_name
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