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

# Устанавливаем зависимости проекта в системное окружение (без виртуального окружения)
RUN poetry config virtualenvs.create false && \
    poetry install --no-root

# Копируем исходный код
COPY . .

EXPOSE 8000

# Используем полный путь к uvicorn
CMD ["/usr/local/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]