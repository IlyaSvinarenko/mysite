FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* ./

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем зависимости проекта
RUN poetry install --no-dev --no-root

# Копируем исходный код
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]