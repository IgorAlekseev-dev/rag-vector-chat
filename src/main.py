from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from src.documents.router import router as documents_router
from src.chat.router import router as chat_router

# Инициализируем приложение
app = FastAPI(title="Vector Search App")

# Подключаем папку с шаблонами (там лежит ваш index.html)
templates = Jinja2Templates(directory="src/templates")

app.include_router(documents_router)
app.include_router(chat_router)

@app.get("/")
async def read_root(request: Request):
    """
    Главная страница: возвращает базовый интерфейс чата.
    """
    return templates.TemplateResponse(request=request, name="index.html")