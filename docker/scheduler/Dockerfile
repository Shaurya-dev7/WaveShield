FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app/
RUN mkdir -p /app/logs /app/data
RUN chown -R appuser:appuser /app

USER appuser

# The scheduler is a background process, no ports to expose.
CMD ["python", "src/scheduler.py"]
