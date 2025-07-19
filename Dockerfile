# Используем официальный образ Python как базовый образ
FROM python:3.11-slim-buster

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем requirements.txt и supercomputersproject-b4130652fa02.json в контейнер
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код приложения в контейнер
COPY main.py .

# Создаем директорию 'graphs' для сохранения графиков
RUN mkdir -p graphs

# Определяем переменную окружения PORT, которую будет использовать Uvicorn
# Cloud Run предоставит порт через эту переменную
ENV PORT 8080

# Команда, которая будет выполняться при запуске контейнера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]