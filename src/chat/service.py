from fastapi.concurrency import run_in_threadpool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from qdrant_client.models import Filter, FieldCondition, MatchValue

from src.config import settings
from src.database import qdrant_client
from src.documents.service import model, COLLECTION_NAME
from src.chat.models import Chat, Message, Document 

llm_client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL
)

def _encode_query(text: str) -> list[float]:
    return model.encode(f"query: {text}").tolist()

# ИЗМЕНИЛИ: теперь функция принимает chat_id
async def generate_answer(user_message: str, chat_id: int) -> str:
    """RAG-поиск с фильтрацией по конкретному chat_id"""
    query_vector = await run_in_threadpool(_encode_query, user_message)

    # Ищем в Qdrant, добавляя жесткий фильтр по chat_id!
    search_result = await qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(key="chat_id", match=MatchValue(value=chat_id))
            ]
        ),
        limit=10
    )

    found_texts = []
    for hit in search_result.points:
        page = hit.payload.get("page", "?")
        text = hit.payload.get("text", "")
        found_texts.append(f"[Страница {page}]: {text}")
        
    context = "\n\n---\n\n".join(found_texts)

    system_prompt = (
        "Ты умный технический помощник. Тебе предоставлен контекст из документации. "
        "Ответь на вопрос пользователя, опираясь ТОЛЬКО на этот контекст. "
        "Отвечай на русском языке, структурированно и понятно. "
        "Если в контексте нет информации для ответа, честно скажи: 'В загруженном документе нет информации об этом', не придумывай."
    )
    
    user_prompt = f"Контекст из документа:\n{context}\n\nВопрос пользователя: {user_message}"

    response = await llm_client.chat.completions.create(
        model=settings.LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4,
        max_tokens=1024
    )

    return response.choices[0].message.content

async def get_all_chats(db: AsyncSession) -> list[Chat]:
    result = await db.execute(select(Chat).order_by(Chat.created_at.desc()))
    return list(result.scalars().all())

async def get_chat(db: AsyncSession, chat_id: int) -> Chat | None:
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    return result.scalar_one_or_none()

async def create_chat(db: AsyncSession, title: str = "Новый чат") -> Chat:
    chat = Chat(title=title)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat

async def get_chat_messages(db: AsyncSession, chat_id: int) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())

async def save_message(db: AsyncSession, chat_id: int, role: str, content: str) -> Message:
    msg = Message(chat_id=chat_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

async def save_document(db: AsyncSession, chat_id: int, filename: str) -> Document:
    """Сохраняет метаданные файла в SQLite"""
    doc = Document(chat_id=chat_id, filename=filename)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc

async def get_chat_documents(db: AsyncSession, chat_id: int) -> list[Document]:
    """Возвращает список всех файлов, загруженных в конкретный чат"""
    result = await db.execute(
        select(Document)
        .where(Document.chat_id == chat_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())