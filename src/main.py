from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

# Инициализируем приложение
app = FastAPI(title="Vector Search App")

# Подключаем папку с шаблонами (там лежит ваш index.html)
templates = Jinja2Templates(directory="src/templates")

@app.get("/")
async def read_root(request: Request):
    """
    Главная страница: возвращает базовый интерфейс чата.
    """
    return templates.TemplateResponse(request=request, name="index.html")