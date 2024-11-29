# Dockerfile для users-service
FROM python:3.10-slim

# Установка зависимостей
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY ./app /app

# Установка переменных окружения
ENV KAFKA_BROKER=kafka:9093
ENV DATABASE_URL=postgresql://user:password@db:5432/users_db

# Запуск FastAPI приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
