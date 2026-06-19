FROM python:3.13-slim-bookworm

WORKDIR /app

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Копируем файлы зависимостей для кэширования слоёв
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости проекта
RUN uv sync --frozen --no-dev

# Копируем только исходный код
COPY src/ ./src/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=src.config.settings \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "src.config.wsgi:application"]
