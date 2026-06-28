FROM python:3.11-slim
WORKDIR /app
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt
COPY assistant ./assistant
COPY config.yaml .
CMD ["uvicorn", "assistant.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
