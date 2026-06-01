from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import settings

# 1. Асинхронный клиент для Qdrant
qdrant_client = AsyncQdrantClient(url=settings.QDRANT_URL)

# 2. Асинхронный движок для SQLite (история чатов)
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Фабрика сессий базы данных (будем использовать как Dependency Injection)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)