# Handles the actual job queue, pushing scrape jobs onto Redis when a claim is submitted and letting
# the worker pop them off one at a time.

from app.core.redis import get_redis
from uuid import UUID
import json

# Queue key name
QUEUE_KEY = "scrape_jobs"

# Queues the job to the left side of a Redis list
async def push_job(report_id: UUID, claim: str) -> None:
    redis_client = get_redis()
    await redis_client.lpush(QUEUE_KEY, json.dumps({"report_id": str(report_id), "claim": claim}))

# Pops jobs from the right side of a Redis list
async def pop_job() -> dict | None:
    redis_client = get_redis()
    popped_job = await redis_client.brpop(QUEUE_KEY, timeout=60)
    if popped_job:
        _, job_data = popped_job
        return json.loads(job_data)
    return None

# Returns the queue length
async def queue_length():
    redis_client = get_redis()
    return await redis_client.llen(QUEUE_KEY)