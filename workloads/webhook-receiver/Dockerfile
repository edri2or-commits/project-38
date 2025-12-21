FROM python:3.11-slim

WORKDIR /app

# Cache buster for forcing rebuild
ARG BUILD_VERSION=unknown
ENV BUILD_VERSION=${BUILD_VERSION}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
