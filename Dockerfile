FROM python:3.11-slim

WORKDIR /app

# System deps for PyMuPDF (gcc) + CJK font support
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Data dir for SQLite + uploads
RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
