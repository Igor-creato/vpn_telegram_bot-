FROM python:3.11-slim

WORKDIR /app

# Обновляем pip
RUN pip install --no-cache-dir --upgrade pip

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы
COPY . .

# Запускаем бота и webhook handler
CMD ["sh", "-c", "python bot.py & python -m uvicorn webhook_handler:app --host 0.0.0.0 --port 8000"]
