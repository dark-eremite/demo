FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка uv для управления зависимостями
RUN pip install --no-cache-dir uv

# Копирование файлов зависимостей
COPY pyproject.toml uv.lock ./

# Установка зависимостей проекта
RUN uv pip install --system -r pyproject.toml

# Копирование исходного кода
COPY . .

# Сборка статических файлов
RUN python manage.py collectstatic --noinput

# Экспорт порта
EXPOSE 8000

# Команда запуска (переопределяется в K8s)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
