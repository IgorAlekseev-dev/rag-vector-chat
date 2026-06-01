# Векторный RAG чат
## Используйте векторный поиск по вашим файлам. Загружайте PDF в чат и спрвшивайте у ИИ содержание этих файлов

## Структура:
```
rag-vector-chat/
├── src/
│   ├── chat/               # Домен: работа с чатами и сообщениями
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py       # SQLAlchemy модели для SQLite (история чатов)
│   │   └── service.py      # Логика RAG и вызов LLM
│   ├── documents/          # Домен: загрузка и обработка PDF
│   │   ├── router.py
│   │   ├── service.py      # Чанкинг, векторизация, вставка в Qdrant
│   │   └── utils.py
│   ├── templates/          # Jinja2 шаблоны
│   │   ├── partials/       # Кусочки HTML для HTMX (сообщения, списки)
│   │   └── index.html      # Основной файл интерфейса
│   ├── config.py           # Глобальные настройки (Pydantic BaseSettings)
│   ├── database.py         # Подключение к SQLite и Qdrant
│   └── main.py             # Точка входа FastAPI
├── .env.example            # Пример секретных ключей
├── docker-compose.yml      # Для запуска Qdrant и всего проекта
├── Dockerfile
└── README.md
```