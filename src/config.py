from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    
    # Настройки Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    
    # Настройки LLM
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL_NAME: str = "llama-3.1-8b-instant"
    
    # Настройки SQLite (используем асинхронный драйвер aiosqlite)
    # База хранится в смонтированной папке data, чтобы переживать пересоздание контейнера.
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/chat_history.db"

    # Заставляем Pydantic читать данные из .env файла
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()