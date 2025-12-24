# Dockerfile for Worker service

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py .

CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 300 worker:app
