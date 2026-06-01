from fastapi import APIRouter, UploadFile, File, Request
from fastapi.templating import Jinja2Templates
from src.documents.service import process_and_store_pdf

router = APIRouter(prefix="/documents", tags=["Documents"])
templates = Jinja2Templates(directory="src/templates")

@router.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...)):
    """
    Принимает файл, отправляет его в сервис обработки и 
    возвращает кусочек HTML (карточку документа) для HTMX.
    """
    # Ждем пока файл нарежется и улетит в Qdrant
    filename = await process_and_store_pdf(file)
    
    # Возвращаем не JSON, а готовый кусок дизайна!
    return templates.TemplateResponse(
        request=request, 
        name="partials/document_card.html", 
        context={"filename": filename}
    )