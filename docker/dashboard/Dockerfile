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
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Start Streamlit without CORS issues and auto-open
CMD ["streamlit", "run", "dashboard/streamlit_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.serverAddress=localhost"]
