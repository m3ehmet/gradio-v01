FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY . .

# Gradio portu
EXPOSE 7860

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:7860/ || exit 1

# Gradio çalıştır
ENTRYPOINT ["python", "app.py"]
