FROM python:3.13-slim-bookworm

WORKDIR /app

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Копируем файлы зависимостей для кэширования слоёв
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости
RUN uv sync --frozen --no-dev

# Копируем исходный код
COPY manage.py ./
COPY config/ ./config/
COPY buildmatapp/ ./buildmatapp/
COPY templates/ ./templates/
COPY static/ ./static/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
