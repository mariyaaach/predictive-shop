# Базовый образ
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt ./requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем содержимое папки `app` в текущую рабочую директорию
COPY app/ ./  

# Запуск
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
