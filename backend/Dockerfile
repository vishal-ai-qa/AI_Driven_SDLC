FROM python:3.12-slim

# System deps: psycopg2 build, tesseract OCR
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    wget \
    gnupg \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium + its system deps in a single layer so
# apt-get update runs before playwright's own apt-get install call.
RUN apt-get update \
    && playwright install chromium --with-deps \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000
