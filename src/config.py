from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    
    # Настройки Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    
    # Настройки LLM
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL_NAME: str = "llama3-8b-8192"
    
    # Настройки SQLite (используем асинхронный драйвер aiosqlite)
    DATABASE_URL: str = "sqlite+aiosqlite:///./chat_history.db"

    # Заставляем Pydantic читать данные из .env файла
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()