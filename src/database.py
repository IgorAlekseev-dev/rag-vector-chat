from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import settings
from src.chat.models import Base 

# 1. Асинхронный клиент для Qdrant
qdrant_client = AsyncQdrantClient(url=settings.QDRANT_URL)

# 2. Асинхронный движок для SQLite
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    """Создает таблицы в базе данных SQLite, если их еще нет"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency Injection для получения сессии базы данных в роутерах"""
    async with AsyncSessionLocal() as session:
        yield session