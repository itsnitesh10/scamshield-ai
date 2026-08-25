FROM python:3.11-slim

# Install Tesseract OCR and required system libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY . .

# Tesseract is installed in the standard Linux location
ENV TESSERACT_CMD=/usr/bin/tesseract

# Cloud platforms provide the PORT environment variable
ENV PORT=8000

# Start FastAPI
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]