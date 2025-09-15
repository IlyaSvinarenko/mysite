from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Получаем URL базы данных из переменных окружения
DB_URL = os.getenv("DB_URL", "postgresql+asyncpg://user:password@localhost:5432/mydatabase")

# Создаем асинхронный движок
engine = create_async_engine(DB_URL, echo=True)

# Создаем фабрику сессий
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Зависимость для получения сессии БД
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()