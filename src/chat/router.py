from fastapi import APIRouter, Request, Form, Depends, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import markdown

from src.database import get_db
from src.chat import service as chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])
templates = Jinja2Templates(directory="src/templates")
templates.env.filters['markdown'] = lambda text: markdown.markdown(text, extensions=['fenced_code', 'tables'])

@router.post("/new")
async def create_new_chat(request: Request, db: AsyncSession = Depends(get_db)):
    all_chats = await chat_service.get_all_chats(db)
    new_title = f"Чат #{len(all_chats) + 1}"
    
    new_chat = await chat_service.create_chat(db, title=new_title)
    all_chats = await chat_service.get_all_chats(db)
    
    # При создании чата документов в нем нет, передаем пустой список []
    return templates.TemplateResponse(
        request=request,
        name="partials/new_chat_response.html",
        context={
            "chats": all_chats,
            "active_chat": new_chat,
            "messages": [],
            "documents": []
        }
    )

@router.get("/{chat_id}")
async def load_chat(request: Request, chat_id: int, db: AsyncSession = Depends(get_db)):
    active_chat = await chat_service.get_chat(db, chat_id)
    all_chats = await chat_service.get_all_chats(db)
    messages = await chat_service.get_chat_messages(db, chat_id)
    
    # Извлекаем из базы список файлов, загруженных в данный чат!
    documents = await chat_service.get_chat_documents(db, chat_id)
    
    return templates.TemplateResponse(
        request=request,
        name="partials/chat_workspace.html",
        context={
            "active_chat": active_chat,
            "chats": all_chats,
            "messages": messages,
            "documents": documents
        }
    )

@router.post("/{chat_id}/message")
async def send_message(request: Request, chat_id: int, message: str = Form(...), db: AsyncSession = Depends(get_db)):
    await chat_service.save_message(db, chat_id, "user", message)
    
    bot_response = await chat_service.generate_answer(message, chat_id)
    
    await chat_service.save_message(db, chat_id, "assistant", bot_response)
    
    return templates.TemplateResponse(
        request=request,
        name="partials/message_pair.html",
        context={
            "user_message": message,
            "bot_response": bot_response
        }
    )