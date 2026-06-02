# ==========================================
# СТАДИЯ 1: Сборщик (Builder)
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

# Включаем компиляцию байт-кода для ускорения запуска Python
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Создаем виртуальное окружение
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Копируем описание зависимостей (ваш pyproject.toml, созданный uv)
COPY pyproject.toml /app/

# Синхронизируем зависимости бэкенда (используем монтируемый кэш uv для скорости)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r pyproject.toml

# Предварительно скачиваем и кэшируем модель e5-small
# Файлы сохранятся в стандартную папку кэша /root/.cache/huggingface
RUN --mount=type=cache,target=/root/.cache/uv \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-small')"


# ==========================================
# СТАДИЯ 2: Продакшен-образ (Final)
# ==========================================
FROM python:3.10-slim

WORKDIR /app

# Копируем собранное виртуальное окружение со всеми библиотеками
COPY --from=builder /app/.venv /app/.venv

# Копируем кэш с уже скачанной моделью e5-small
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface

# Добавляем пути нашего виртуального окружения в системный PATH
ENV PATH="/app/.venv/bin:$PATH"

# Копируем исходный код бэкенда и настройки
COPY src/ /app/src/
COPY .env /app/.env

# Открываем порт
EXPOSE 8000

# Запускаем приложение через uvicorn из нашего виртуального окружения
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]