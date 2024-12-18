# Базовый образ
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt ./requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY app ./app


# Указываем, откуда запускать приложение
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
