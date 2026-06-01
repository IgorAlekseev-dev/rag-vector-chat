from fastapi.concurrency import run_in_threadpool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.chat.models import Chat, Message
from src.config import settings
from src.database import qdrant_client
from src.documents.service import model, COLLECTION_NAME

# Инициализируем асинхронный клиент OpenAI (Groq полностью поддерживает этот формат)
llm_client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL
)

def _encode_query(text: str) -> list[float]:
    """
    Модель e5-small требует префикс 'query: ' для вопросов 
    и 'passage: ' для документов.
    """
    return model.encode(f"query: {text}").tolist()

async def generate_answer(user_message: str) -> str:
    """Полный цикл RAG: поиск в Qdrant -> промпт -> ответ от LLM"""
    
    # 1. Векторизуем вопрос пользователя (в пуле потоков)
    query_vector = await run_in_threadpool(_encode_query, user_message)

# 2. Ищем топ-10 (увеличили лимит, чтобы захватить больше сути документа)
    search_result = await qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=10
    )

    # 3. Формируем контекст с указанием страниц!
    found_texts = []
    for hit in search_result.points:
        page = hit.payload.get("page", "?")
        text = hit.payload.get("text", "")
        # Теперь нейросеть будет видеть текст вот так: [Страница 15]: Подводя итоги...
        found_texts.append(f"[Страница {page}]: {text}")
        
    context = "\n\n---\n\n".join(found_texts)

    # 4. Формируем строгий промпт (ту самую "невидимую инструкцию")
    system_prompt = (
        "Ты умный технический помощник. Тебе предоставлен контекст из документации. "
        "Ответь на вопрос пользователя, опираясь ТОЛЬКО на этот контекст. "
        "Отвечай на русском языке, структурированно и понятно. "
        "Если в контексте нет информации для ответа, честно скажи: 'В загруженном документе нет информации об этом', не придумывай."
    )
    
    user_prompt = f"Контекст из документа:\n{context}\n\nВопрос пользователя: {user_message}"

    # 5. Отправляем запрос в нейросеть
    response = await llm_client.chat.completions.create(
        model=settings.LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4, # Низкая температура, чтобы модель была точной и не фантазировала
        max_tokens=1024
    )

    return response.choices[0].message.content

async def get_all_chats(db: AsyncSession) -> list[Chat]:
    """Возвращает список всех чатов, сортируя их по дате создания"""
    result = await db.execute(select(Chat).order_by(Chat.created_at.desc()))
    return list(result.scalars().all())

async def get_chat(db: AsyncSession, chat_id: int) -> Chat | None:
    """Находит один чат по его ID"""
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    return result.scalar_one_or_none()

async def create_chat(db: AsyncSession, title: str = "Новый чат") -> Chat:
    """Создает новую сессию чата"""
    chat = Chat(title=title)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat

async def get_chat_messages(db: AsyncSession, chat_id: int) -> list[Message]:
    """Возвращает всю историю сообщений для выбранного чата"""
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())

async def save_message(db: AsyncSession, chat_id: int, role: str, content: str) -> Message:
    """Сохраняет сообщение (пользователя или ИИ) в базу данных"""
    msg = Message(chat_id=chat_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg