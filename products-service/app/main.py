from sqlalchemy.orm import selectinload
import uvicorn
from sqlalchemy import update
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from fastapi import FastAPI, Depends, HTTPException, status, logger
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import selectinload
from typing import List
from .schemas import ProductsOut, ProductsCreate
from .model import Products

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при запуске приложения
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Приложение будет работать в этом месте

    # Действия при завершении приложения
    await engine.dispose()

# Создание приложения
app = FastAPI(lifespan=lifespan)


@app.post("/products", response_model=ProductOut)
async def create_product_endpoint(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создает новый продукт после проверки пользователя с ролью `seller`.

    Args:
        product (ProductCreate): Данные продукта.
        db (AsyncSession): Сессия базы данных.

    Returns:
        ProductOut: Созданный продукт.
    """
    try:
        new_product = await create_product(db, product)
        return new_product
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Ошибка создания продукта: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )