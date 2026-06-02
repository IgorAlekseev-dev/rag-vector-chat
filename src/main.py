from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import markdown

from src.database import init_db, get_db
from src.documents.router import router as documents_router
from src.chat.router import router as chat_router
from src.chat import service as chat_service
from src.documents.service import init_qdrant

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск сервера: инициализация базы данных SQLite...")
    await init_db()
    print("Запуск сервера: проверка и инициализация коллекции Qdrant...")
    await init_qdrant()
    yield
    print("Выключение сервера...")

app = FastAPI(title="Vector Search App", lifespan=lifespan)
templates = Jinja2Templates(directory="src/templates")
templates.env.filters['markdown'] = lambda text: markdown.markdown(text, extensions=['fenced_code', 'tables'])

app.include_router(documents_router)
app.include_router(chat_router)

@app.get("/")
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    chats = await chat_service.get_all_chats(db)
    
    if not chats:
        active_chat = await chat_service.create_chat(db, "Мой первый чат")
        chats = [active_chat]
    else:
        active_chat = chats[0]
        
    messages = await chat_service.get_chat_messages(db, active_chat.id)
    
    # Подгружаем документы для активного чата на главной странице!
    documents = await chat_service.get_chat_documents(db, active_chat.id)
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "chats": chats,
            "active_chat": active_chat,
            "messages": messages,
            "documents": documents
        }
    )