# Use stable Debian Bookworm slim variant for a minimal footprint
FROM python:3.10-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install runtime dependencies for OpenCV (headless version needs glib and gomp for DNN/parallel execution)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pre-downloaded models if present, and application code
COPY ./models ./models
COPY ./app ./app

# Pre-download/verify models during image build so they are baked in
RUN python -c "from app.verifier import download_models_if_missing; download_models_if_missing()"

# Expose the application port
EXPOSE 8000

# Start Gunicorn managing Uvicorn workers for production scaling
CMD ["sh", "-c", "gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT"]