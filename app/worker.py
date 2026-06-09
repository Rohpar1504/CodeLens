import asyncio
import httpx
from app.webhooks.queue import dequeue_review_job
from app.webhooks.auth import get_installation_token
from app.webhooks.diff_parser import parse_pull_request_files
from app.rag.indexer import index_repository
from app.rag.retriever import retrieve_context
from app.review.llm import review_pull_request
from app.review.poster import post_review_comments
from app.db.installations import get_or_create_repo_settings
from app.db.repo_config import fetch_repo_config
from app.db.database import init_db


async def process_job(job: dict):
    print(f"[worker] Processing PR #{job['pull_number']} in {job['repo_full_name']}")

    # Get GitHub token
    token = await get_installation_token(job["installation_id"])
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    # Step 1 — Load repo settings and config
    settings = await get_or_create_repo_settings(
        job["repo_full_name"],
        job["installation_id"],
    )
    config = await fetch_repo_config(job["repo_full_name"], token)

    if not config.get("enabled", True):
        print(f"[worker] CodeLens disabled for {job['repo_full_name']}, skipping")
        return

    excluded_paths = config.get("exclude", [])
    severity_threshold = config.get("severity_threshold", "suggestion")
    print(f"[worker] Config loaded — excluded: {excluded_paths}, threshold: {severity_threshold}")

    # Step 2 — Index the repo
    print(f"[worker] Indexing {job['repo_full_name']}...")
    await index_repository(job["repo_full_name"], token)

    # Step 3 — Fetch PR diff
    url = (
        f"https://api.github.com/repos/{job['repo_full_name']}"
        f"/pulls/{job['pull_number']}/files"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        pr_files = response.json()

    # Step 4 — Parse diff, respecting excluded paths
    hunks = parse_pull_request_files(pr_files)
    hunks = [
        h for h in hunks
        if not any(h.filename.startswith(ex) for ex in excluded_paths)
    ]
    print(f"[worker] Found {len(hunks)} reviewable hunks after exclusions")

    # Step 5 — Retrieve RAG context for each hunk
    context_by_hunk = []
    for hunk in hunks:
        diff_text = "\n".join(hunk.added_lines)
        if diff_text.strip():
            context = await retrieve_context(job["repo_full_name"], diff_text, k=3)
        else:
            context = []
        context_by_hunk.append(context)

    # Step 6 — LLM review
    print(f"[worker] Running LLM review...")
    all_comments = await review_pull_request(hunks, context_by_hunk)

    # Step 7 — Filter by severity threshold
    severity_order = {"suggestion": 0, "warning": 1, "error": 2}
    threshold_level = severity_order.get(severity_threshold, 0)
    filtered_comments = [
        c for c in all_comments
        if severity_order.get(c["severity"], 0) >= threshold_level
    ]
    print(f"[worker] {len(filtered_comments)} comments after severity filter")

    # Step 8 — Post to GitHub
    await post_review_comments(
        repo_full_name=job["repo_full_name"],
        pull_number=job["pull_number"],
        head_sha=job["head_sha"],
        comments=filtered_comments,
        token=token,
    )

    print(f"[worker] Done with PR #{job['pull_number']}")


async def run_worker():
    # Initialize database on startup
    await init_db()
    print("[worker] Database initialized")
    print("[worker] Starting. Waiting for jobs...")

    while True:
        job = await dequeue_review_job()
        if job is None:
            continue
        try:
            await process_job(job)
        except Exception as e:
            print(f"[worker] Error processing job: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_worker())