FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORTAINER_WEBHOOK_URL="http://host.docker.internal:9000/api/webhooks/34870f1d-267d-4bc4-b7cb-9f6c11146aed"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
