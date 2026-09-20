# Production Dockerfile for Apex Wireless Hybrid GEAP Multi-Agent Backend
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Environment variables for Cloud Run
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_GENAI_USE_VERTEXAI=1
ENV GOOGLE_CLOUD_LOCATION=us-central1
ENV APEX_ENFORCE_AUTH=1

EXPOSE 8080

# Run FastAPI microservice via Uvicorn
CMD exec uvicorn server:app --host 0.0.0.0 --port ${PORT} --workers 2
