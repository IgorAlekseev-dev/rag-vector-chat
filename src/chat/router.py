from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from src.chat.service import generate_answer

router = APIRouter(prefix="/chat", tags=["Chat"])
templates = Jinja2Templates(directory="src/templates")

@router.post("/message")
async def send_message(request: Request, message: str = Form(...)):
    """
    Принимает сообщение от пользователя, генерирует ответ 
    и возвращает кусок HTML с двумя сообщениями (вопрос и ответ)
    """
    # Получаем ответ от RAG-системы
    bot_response = await generate_answer(message)
    
    # Возвращаем шаблон с перепиской
    return templates.TemplateResponse(
        request=request, 
        name="partials/message.html", 
        context={
            "user_message": message,
            "bot_response": bot_response
        }
    )