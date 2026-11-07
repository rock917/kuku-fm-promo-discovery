# Dockerfile for Azure App Service / Azure Container Apps
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from buffering stdout/stderr and writing .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (Azure App Service typically defaults to 8000 or uses $PORT)
EXPOSE 8000

# Run FastAPI via Gunicorn with Uvicorn workers
CMD exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api:app --bind 0.0.0.0:${PORT}
