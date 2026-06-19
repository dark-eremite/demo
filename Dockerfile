FROM python:3.12-slim-bookworm

WORKDIR /app

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Копируем файлы зависимостей первыми для использования кэша
COPY pyproject.toml uv.lock ./

# Синхронизируем зависимости и устанавливаем проект
# --frozen гарантирует использование точных версий из uv.lock
RUN uv sync --frozen --no-install-project --no-dev

# Копируем исходный код проекта
COPY . .

# Устанавливаем сам проект в режиме production
RUN uv sync --frozen --no-dev

# Переменные окружения для Django
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    HOST=0.0.0.0 \
    PORT=8000

# Открываем порт
EXPOSE 8000

# Команда запуска (gunicorn будет установлен через uv sync, если он есть в зависимостях, 
# иначе используем встроенный сервер для dev, но лучше добавить gunicorn в pyproject.toml)
# Для демонстрации используем gunicorn, предполагая, что он добавлен в зависимости.
# Если нет, замените на: ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
