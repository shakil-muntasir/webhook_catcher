# Dreamcatcher API

The primary goal of this microservice is to act as a secure relay or middleman for webhook events. By using Dreamcatcher, you can avoid exposing your original webhook URL directly—helpful for privacy, security, or when operating behind a firewall. Additionally, if the incoming webhook data does not match the requirements of your downstream service, Dreamcatcher allows you to intercept, inspect, and customize the payload before forwarding, ensuring compatibility and flexibility.

Dreamcatcher is a FastAPI-based microservice that provides two main endpoints:

- `/` (GET): Returns a motivational quote (from ZenQuotes API or a fallback).
- `/github` (POST): Receives GitHub webhook events for published Docker multi-arch manifests and forwards them to a configured webhook URL.
> **Note:** You can extend Dreamcatcher by adding your own FastAPI endpoints to suit your specific needs. Simply define new routes in the codebase as required.

## Features

- **Rate Limiting:** Protects endpoints from abuse using `slowapi`.
- **Webhook Forwarding:** Forwards specific GitHub Container Registry publish events.
- **Motivational Quotes:** Fetches a random quote from ZenQuotes.

---

## Usage

### 1. Environment Variable

Set the `WEBHOOK_URL` environment variable to the URL where you want to forward qualifying GitHub webhook events.

Example:
```sh
export WEBHOOK_URL="https://your-webhook-receiver.example.com/endpoint"
```

### 2. Running Locally

Install dependencies:
```sh
pip install -r requirements.txt
```

Start the server:
```sh
uvicorn main:app --host 0.0.0.0 --port 8080
```

---

## API Endpoints

### GET `/`

Returns a motivational quote.

**Example:**
```sh
curl http://localhost:8080/
```

**Response:**
```json
{
  "quote": "The only limit to our realization of tomorrow is our doubts of today. — Franklin D. Roosevelt"
}
```

---

### POST `/github`

Receives GitHub webhook payloads. Only forwards events where:

- `action` is `"published"`
- `media_type` is `"application/vnd.docker.distribution.manifest.list.v2+json"`

> **Note:** The forwarding logic is tailored for Docker multi-arch manifest publish events. If your use case differs, update the filtering conditions in the code to match your specific event types and payload structure.

**Example:**
```sh
curl -X POST http://localhost:8080/github \
  -H "Content-Type: application/json" \
  -d '{"action":"published","repository":{"full_name":"owner/repo"},"package":{"package_version":{"id":"123","container_metadata":{"manifest":{"media_type":"application/vnd.docker.distribution.manifest.list.v2+json"}}}}}'
```

---

## Docker

### Build the Docker image

```sh
docker build -t dreamcatcher .
```

### Run the container

```sh
docker run -d \
  -e WEBHOOK_URL="https://your-webhook-receiver.example.com/endpoint" \
  -p 8080:8080 \
  --name dreamcatcher \
  dreamcatcher
```

The API will be available at [http://localhost:8080](http://localhost:8080).

---

## License

Dreamcatcher is open source and released under the [MIT License](LICENSE). It is 100% free to use, modify, and distribute.