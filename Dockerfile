# Dockerfile — replace the CMD line at the bottom

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p models

EXPOSE 8000

# Give 5 minutes (300s) for app to start (ML libraries take time to initialize)
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Use shell form to properly handle PORT environment variable
CMD sh -c 'uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}'