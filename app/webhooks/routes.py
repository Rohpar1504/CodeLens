import json
import httpx
from fastapi import APIRouter, Request
from app.webhooks.security import verify_webhook_signature
from app.webhooks.diff_parser import parse_pull_request_files
from app.webhooks.queue import enqueue_review_job
from app.db.installations import save_installation, deactivate_installation

router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):
    # 1. Verify signature
    body = await verify_webhook_signature(request)
    payload = json.loads(body)

    event_type = request.headers.get("X-GitHub-Event", "")

    # 2. Handle app installation events
    if event_type == "installation":
        action = payload.get("action", "")
        installation = payload["installation"]
        account = installation["account"]

        if action == "created":
            await save_installation(
                installation_id=installation["id"],
                account_login=account["login"],
                account_type=account["type"],
            )
            return {"status": "installation saved"}

        elif action == "deleted":
            await deactivate_installation(installation["id"])
            return {"status": "installation deactivated"}

    # 3. Handle pull request events
    if event_type != "pull_request":
        return {"status": "ignored", "event": event_type}

    action = payload.get("action", "")
    if action not in ("opened", "synchronize"):
        return {"status": "ignored", "action": action}

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

    await enqueue_review_job(job)
    return {"status": "queued", "pull_number": pr["number"]}