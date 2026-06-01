import os
import uuid
import tempfile
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client.models import VectorParams, Distance, PointStruct

from src.database import qdrant_client

# Загружаем модель один раз при старте
model = SentenceTransformer('intfloat/multilingual-e5-small')
COLLECTION_NAME = "docs_collection"

async def init_qdrant():
    """Создает коллекцию в Qdrant, если её еще нет."""
    if not await qdrant_client.collection_exists(COLLECTION_NAME):
        await qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

def _encode_text(texts: list[str]) -> list[list[float]]:
    """Функция для векторизации (работает на CPU, поэтому вызовем ее в отдельном потоке)"""
    prefixed = [f"passage: {t}" for t in texts]
    return model.encode(prefixed).tolist()

async def process_and_store_pdf(file: UploadFile) -> str:
    """Полный цикл: чтение PDF -> Чанкинг -> Эмбеддинги -> Сохранение в Qdrant"""
    await init_qdrant()
    
    # Сохраняем загруженный файл во временную папку ОС
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Чтение PDF
        loader = PyPDFLoader(tmp_path)
        docs = await run_in_threadpool(loader.load)

        # РАЗБИВАЕМ ПО-УМНОМУ (split_documents сохраняет метаданные страниц!)
        # Чуть увеличим размер чанка, чтобы мысль не обрывалась
        splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=150)
        chunked_docs = splitter.split_documents(docs)

        # Вытаскиваем только тексты для векторизации
        texts = [doc.page_content for doc in chunked_docs]
        
        # Векторизуем
        vectors = await run_in_threadpool(_encode_text, texts)

        # Подготавливаем точки для Qdrant (ТЕПЕРЬ С НОМЕРОМ СТРАНИЦЫ!)
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "text": doc.page_content, 
                    "filename": file.filename,
                    "page": doc.metadata.get("page", 0) + 1  # PyPDF считает страницы с нуля, прибавляем 1
                }
            )
            for doc, vec in zip(chunked_docs, vectors)
        ]

        # Грузим в базу
        if points:
            await qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
        
        return file.filename
    finally:
        # Обязательно удаляем временный файл
        os.remove(tmp_path)