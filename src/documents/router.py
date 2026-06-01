from fastapi import APIRouter, UploadFile, File, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.documents.service import process_and_store_pdf
from src.chat import service as chat_service

router = APIRouter(prefix="/documents", tags=["Documents"])
templates = Jinja2Templates(directory="src/templates")

@router.post("/{chat_id}/upload")
async def upload_document(request: Request, chat_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Принимает файл для выбранного чата, векторизует и возвращает обновленный список файлов"""
    
    # 1. Сохраняем метаданные файла в SQLite
    await chat_service.save_document(db, chat_id, file.filename)
    
    # 2. Обрабатываем и пишем векторы в Qdrant с привязкой к chat_id
    await process_and_store_pdf(file, chat_id)
    
    # Получаем обновленный список документов
    documents = await chat_service.get_chat_documents(db, chat_id)
    
    # Возвращаем обновленный список файлов в правое меню
    return templates.TemplateResponse(
        request=request, 
        name="partials/document_list_items.html", 
        context={"documents": documents}
    )