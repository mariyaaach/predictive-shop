import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
#надо норм работать с env, но какого то фига вообще не получается, так что пускай тут стоит
DATABASE_URL = "postgresql+asyncpg://login:password@localhost:port/name_bd"

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def get_db():
    async with async_session() as session:
        yield session