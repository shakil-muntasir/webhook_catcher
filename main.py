from fastapi import FastAPI, Request
import httpx
import os
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

PORTAINER_WEBHOOK_URL = os.getenv("PORTAINER_WEBHOOK_URL")
if not PORTAINER_WEBHOOK_URL:
    raise RuntimeError(
        "PORTAINER_WEBHOOK_URL environment variable is not set.")

logging.info(f"Using Portainer Webhook URL: {PORTAINER_WEBHOOK_URL}")


@app.get("/")
async def root():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://zenquotes.io/api/random")
            if res.status_code == 200:
                data = res.json()[0]
                return {"quote": f"{data['q']} — {data['a']}"}
    except Exception:
        logging.warning("Failed to fetch quote from external API.")
    return {"quote": "Remember: 'The only limit to our realization of tomorrow is our doubts of today.' - Franklin D. Roosevelt"}


@app.post("/github")
async def github_webhook(request: Request):
    try:
        payload = await request.json()

        action = payload.get("action")
        repo = payload.get("repository", {}).get("full_name", "unknown")
        version_id = payload.get("package", {}).get(
            "package_version", {}).get("id", "n/a")
        media_type = (
            payload.get("package", {})
            .get("package_version", {})
            .get("container_metadata", {})
            .get("manifest", {})
            .get("media_type", "")
        )

        logging.info(
            f"[GitHub] Action: {action} | Repo: {repo} | Version ID: {version_id} | Media Type: {media_type}")

        if action != "published":
            return {"status": "ignored", "reason": "not a publish event"}

        if media_type != "application/vnd.docker.distribution.manifest.list.v2+json":
            return {"status": "ignored", "reason": "not multi-arch manifest"}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                str(PORTAINER_WEBHOOK_URL),
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            logging.info(f"[Forwarded] Status: {resp.status_code}")
            return {"status": "forwarded", "portainer_status": resp.status_code}

    except Exception as e:
        logging.error(f"[Error] {str(e)}")
        return {"status": "error", "error": str(e)}
