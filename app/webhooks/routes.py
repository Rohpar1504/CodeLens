import json
import httpx
from fastapi import APIRouter, Request
from app.webhooks.security import verify_webhook_signature
from app.webhooks.diff_parser import parse_pull_request_files
from app.webhooks.queue import enqueue_review_job

router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):
    # 1. Verify signature (raises 401 if invalid)
    body = await verify_webhook_signature(request)
    payload = json.loads(body)

    event_type = request.headers.get("X-GitHub-Event", "")

    # 2. Only handle pull_request events with action opened/synchronize
    if event_type != "pull_request":
        return {"status": "ignored", "event": event_type}

    action = payload.get("action", "")
    if action not in ("opened", "synchronize"):
        return {"status": "ignored", "action": action}

    # 3. Extract the info we need
    pr = payload["pull_request"]
    repo = payload["repository"]
    installation_id = payload["installation"]["id"]

    job = {
        "installation_id": installation_id,
        "repo_owner": repo["owner"]["login"],
        "repo_name": repo["name"],
        "repo_full_name": repo["full_name"],
        "pull_number": pr["number"],
        "head_sha": pr["head"]["sha"],
        "base_sha": pr["base"]["sha"],
        "pr_title": pr["title"],
    }

    # 4. Push to Redis queue (worker will pick it up)
    await enqueue_review_job(job)

    return {"status": "queued", "pull_number": pr["number"]}