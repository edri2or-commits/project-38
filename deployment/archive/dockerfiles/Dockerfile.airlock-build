# Dockerfile for Airlock service

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY airlock.py .

CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 60 airlock:app
