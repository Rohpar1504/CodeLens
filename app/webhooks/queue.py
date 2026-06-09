import json
import redis.asyncio as aioredis
from app.config import settings

REVIEW_QUEUE = "review_queue"


def get_redis():
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def enqueue_review_job(job: dict) -> None:
    """Push a review job onto the Redis queue."""
    async with get_redis() as r:
        await r.lpush(REVIEW_QUEUE, json.dumps(job))


async def dequeue_review_job() -> dict | None:
    """
    Blocking pop — waits up to 5 seconds for a job.
    Returns the job dict or None on timeout.
    """
    try:
        async with get_redis() as r:
            result = await r.brpop(REVIEW_QUEUE, timeout=5)
        if result is None:
            return None
        _, raw = result
        return json.loads(raw)
    except Exception:
        return None