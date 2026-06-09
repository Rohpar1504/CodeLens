import asyncio
import json
import httpx
from app.webhooks.queue import dequeue_review_job
from app.webhooks.auth import get_installation_token
from app.webhooks.diff_parser import parse_pull_request_files


async def process_job(job: dict):
    print(f"[worker] Processing PR #{job['pull_number']} in {job['repo_full_name']}")

    # Get a short-lived token for this installation
    token = await get_installation_token(job["installation_id"])

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    # Fetch the list of changed files + patches
    url = (
        f"https://api.github.com/repos/{job['repo_full_name']}"
        f"/pulls/{job['pull_number']}/files"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        pr_files = response.json()

    # Parse the diff
    hunks = parse_pull_request_files(pr_files)
    print(f"[worker] Found {len(hunks)} diff hunks across {len(pr_files)} files")
    for hunk in hunks:
        print(f"  {hunk.filename} @ line {hunk.start_line}: "
              f"+{len(hunk.added_lines)} -{len(hunk.removed_lines)} lines")

    # Phase 3 will add: RAG retrieval → LLM review → post comments


async def run_worker():
    print("[worker] Starting. Waiting for jobs...")
    while True:
        job = await dequeue_review_job()
        if job is None:
            continue  # timeout, loop again
        try:
            await process_job(job)
        except Exception as e:
            print(f"[worker] Error processing job: {e}")


if __name__ == "__main__":
    asyncio.run(run_worker())