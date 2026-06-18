# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем uv
RUN pip install --no-cache-dir uv

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости с помощью uv
RUN uv sync --frozen --no-dev

# Копируем весь проект
COPY . .

# Собираем статику (будет переопределено в initContainer при необходимости)
RUN python manage.py collectstatic --noinput --clear || true

# Открываем порт для Gunicorn
EXPOSE 8000

# Запускаем приложение через Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
