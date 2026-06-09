import asyncio
import httpx
from app.webhooks.queue import dequeue_review_job
from app.webhooks.auth import get_installation_token
from app.webhooks.diff_parser import parse_pull_request_files
from app.rag.indexer import index_repository
from app.rag.retriever import retrieve_context


async def process_job(job: dict):
    print(f"[worker] Processing PR #{job['pull_number']} in {job['repo_full_name']}")

    # Get a short-lived token for this installation
    token = await get_installation_token(job["installation_id"])

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    # Step 1 — Index the repo (skip if already indexed)
    print(f"[worker] Indexing {job['repo_full_name']}...")
    await index_repository(job["repo_full_name"], token)

    # Step 2 — Fetch the PR diff
    url = (
        f"https://api.github.com/repos/{job['repo_full_name']}"
        f"/pulls/{job['pull_number']}/files"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        pr_files = response.json()

    # Step 3 — Parse the diff into hunks
    hunks = parse_pull_request_files(pr_files)
    print(f"[worker] Found {len(hunks)} diff hunks across {len(pr_files)} files")

    # Step 4 — Retrieve relevant context for each hunk
    for hunk in hunks:
        diff_text = "\n".join(hunk.added_lines)
        if not diff_text.strip():
            continue

        context = await retrieve_context(job["repo_full_name"], diff_text, k=3)
        print(f"[worker] Hunk in {hunk.filename} — retrieved {len(context)} context chunks")
        for c in context:
            print(f"  → {c['metadata']['filepath']}:{c['metadata']['start_line']} "
                  f"({c['metadata']['name']}) distance={c['distance']:.3f}")

    # Phase 4 will add: LLM review → post comments


async def run_worker():
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