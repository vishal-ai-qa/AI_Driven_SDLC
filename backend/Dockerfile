FROM python:3.12-slim

# Install system deps for Playwright + psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    wget \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers for backend execution agent
RUN playwright install chromium --with-deps

COPY . .

EXPOSE 8000
