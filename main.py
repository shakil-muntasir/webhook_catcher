from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import os
import logging
import traceback

# --- App and Rate Limiter Setup ---
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL environment variable is not set.")

logging.info(f"Using Webhook URL: {WEBHOOK_URL}")


# --- Rate Limit Exception Handler ---
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429, content={"detail": "Rate limit exceeded. Please slow down."}
    )


# --- GET "/" Route with Motivational Quote ---
@app.get("/")
@limiter.limit("10/minute")
async def root(request: Request):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://zenquotes.io/api/random", timeout=5)
            if res.status_code == 200:
                data = res.json()[0]
                return {"quote": f"{data['q']} — {data['a']}"}
    except Exception:
        logging.warning("Failed to fetch quote from external API.")
    return {
        "quote": "Remember: 'The only limit to our realization of tomorrow is our doubts of today.' - Franklin D. Roosevelt"
    }


# --- POST "/github" Route for GitHub Webhooks ---
@app.post("/github")
@limiter.limit("5/minute")
async def github_webhook(request: Request):
    try:
        payload = await request.json()

        action = payload.get("action")
        repo = payload.get("repository", {}).get("full_name", "unknown")
        version_id = (
            payload.get("package", {}).get("package_version", {}).get("id", "n/a")
        )
        media_type = (
            payload.get("package", {})
            .get("package_version", {})
            .get("container_metadata", {})
            .get("manifest", {})
            .get("media_type", "")
        )

        logging.info(
            f"[GitHub] Action: {action} | Repo: {repo} | Version ID: {version_id} | Media Type: {media_type}"
        )

        if action != "published":
            return {"status": "ignored", "reason": "not a publish event"}

        if media_type != "application/vnd.docker.distribution.manifest.list.v2+json":
            return {"status": "ignored", "reason": "not multi-arch manifest"}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                str(WEBHOOK_URL),
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            logging.info(
                f"[Forwarded] Receiver responded with status: {resp.status_code}"
            )
            return {"status": "forwarded", "status": resp.status_code}

    except Exception as e:
        logging.error("[Error] Exception during webhook processing")
        logging.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "trace": traceback.format_exc(),
            },
        )
