FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && playwright install chromium
COPY *.py .
ENV PORT=8080
EXPOSE 8080
CMD ["python", "server.py"]
